import base64
import os
import subprocess
import tempfile

from odoo import models, fields, api

DIANA_UID = 64
STACEY_UID = 69
STACEY_EMAIL = 'documentacion@amunet.com.mx'
PARAM_CARPETA = 'amunet_doc_compartida.stacey_folder_url'
NEXTCLOUD_URL = 'https://next.amunet.com.mx/apps/files/files/377815?dir=/Drive-Migration/LFIA%20PDF/Nueva%20versi%C3%B3n'


class DocActualizarWizard(models.TransientModel):
    _name = 'amunet.doc.actualizar.wizard'
    _description = 'Actualizar manual aprobado en sistema de documentos'

    doc_id = fields.Many2one('amunet.doc.compartida', required=True, readonly=True)
    doc_name = fields.Char(related='doc_id.name', readonly=True)
    carpeta_url = fields.Char(
        default=lambda self: self.env['ir.config_parameter'].sudo().get_param(PARAM_CARPETA, ''),
        readonly=True)
    tiene_carpeta = fields.Boolean(compute='_compute_tiene_carpeta')

    @api.depends('carpeta_url')
    def _compute_tiene_carpeta(self):
        for rec in self:
            rec.tiene_carpeta = bool((rec.carpeta_url or '').strip())

    def action_aceptar(self):
        doc = self.doc_id
        carpeta = (self.env['ir.config_parameter'].sudo()
                   .get_param(PARAM_CARPETA, '')).strip()

        if carpeta:
            self._subir_a_nextcloud_y_notificar(doc, carpeta)
        else:
            self._enviar_pdf_por_correo(doc)

        # Marcar actividad de Diana como hecha
        doc.activity_ids.filtered(
            lambda a: a.user_id.id == DIANA_UID
            and 'aprobado' in (a.summary or '').lower()
        ).action_done()

        return {'type': 'ir.actions.act_window_close'}

    def action_posponer(self):
        return {'type': 'ir.actions.act_window_close'}

    def _subir_a_nextcloud_y_notificar(self, doc, carpeta_rclone):
        if not doc.manual_file:
            return

        # Escribir PDF a archivo temporal y subirlo con rclone
        filename = doc.manual_filename or f'{doc.name}.pdf'
        pdf_bytes = base64.b64decode(doc.manual_file)

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name

        try:
            resultado = subprocess.run(
                ['rclone', 'copyto', tmp_path, f'{carpeta_rclone}/{filename}'],
                capture_output=True, text=True, timeout=60
            )
            exito = resultado.returncode == 0
        finally:
            os.unlink(tmp_path)

        if exito:
            self._notificar_stacey_subida(doc, filename)
            doc.message_post(
                body=f'✅ PDF subido a <a href="{NEXTCLOUD_URL}">LFIA PDF / Nueva versión</a> '
                     f'como <b>{filename}</b>. Stacy fue notificada para archivarlo.',
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )
        else:
            doc.message_post(
                body=f'⚠️ Error al subir el PDF a Nextcloud: {resultado.stderr}. '
                     f'Se envió el PDF por correo a Stacy como respaldo.',
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )
            self._enviar_pdf_por_correo(doc)

    def _notificar_stacey_subida(self, doc, filename):
        cuerpo = (
            f'<p>Hola Stacy,</p>'
            f'<p>El manual <b>{doc.name}</b> ha sido revisado y <b>aprobado</b> por Calidad.</p>'
            f'<p>El PDF (<b>{filename}</b>) ya fue subido a la carpeta '
            f'<a href="{NEXTCLOUD_URL}">LFIA PDF / Nueva versión</a> en Nextcloud.</p>'
            f'<p>Por favor archívalo en la carpeta correspondiente cuando puedas.</p>'
            f'<p>Gracias.</p>'
        )
        self.env['mail.mail'].sudo().create({
            'subject': f'Manual subido a Nextcloud (pendiente archivar): {doc.name}',
            'body_html': cuerpo,
            'email_to': STACEY_EMAIL,
'author_id': self.env.user.partner_id.id,
        }).send()

    def _enviar_pdf_por_correo(self, doc):
        attachment_ids = []
        if doc.manual_file:
            attachment = self.env['ir.attachment'].sudo().create({
                'name': doc.manual_filename or f'{doc.name}.pdf',
                'datas': doc.manual_file,
                'res_model': 'amunet.doc.compartida',
                'res_id': doc.id,
                'mimetype': 'application/pdf',
            })
            attachment_ids = [attachment.id]

        cuerpo = (
            f'<p>Hola Stacy,</p>'
            f'<p>El manual <b>{doc.name}</b> ha sido revisado y <b>aprobado</b> por Calidad.</p>'
            f'<p>Te adjuntamos el PDF para que lo archives en la carpeta correspondiente.</p>'
            f'<p>Gracias.</p>'
        )
        self.env['mail.mail'].sudo().create({
            'subject': f'Manual aprobado para archivar: {doc.name}',
            'body_html': cuerpo,
            'email_to': STACEY_EMAIL,
            'author_id': self.env.user.partner_id.id,
            'attachment_ids': [(6, 0, attachment_ids)],
        }).send()

        doc.message_post(
            body=f'📧 PDF enviado por correo a Stacy para archivar manualmente.',
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
