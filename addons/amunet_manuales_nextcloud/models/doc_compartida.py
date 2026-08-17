# -*- coding: utf-8 -*-
import base64
import logging
from urllib.parse import quote

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DocCompartidaNextcloud(models.Model):
    _inherit = 'amunet.doc.compartida'

    url_nextcloud = fields.Char(
        string='Enlace Nextcloud',
        readonly=True,
        help='URL del PDF en Nextcloud. Se llena automaticamente al aprobar el manual.',
    )
    enlace_pdf = fields.Html(
        string='PDF',
        compute='_compute_enlace_pdf',
        sanitize=False,
        store=False,
    )

    @api.depends('url_nextcloud', 'manual_filename', 'manual_file')
    def _compute_enlace_pdf(self):
        for rec in self:
            if not rec.manual_filename:
                rec.enlace_pdf = False
                continue
            if rec.url_nextcloud:
                url = rec.url_nextcloud
            elif rec.manual_file:
                url = (
                    '/web/content?model=amunet.doc.compartida'
                    '&id=%d&field=manual_file&filename=%s&download=true'
                ) % (rec.id, rec.manual_filename)
            else:
                rec.enlace_pdf = False
                continue
            rec.enlace_pdf = (
                '<a href="%s" target="_blank" style="white-space:nowrap">'
                '<i class="fa fa-download" style="margin-right:5px"></i>%s</a>'
            ) % (url, rec.manual_filename)

    def write(self, vals):
        candidatos_aprobar = []
        candidatos_reemplazar = []

        if vals.get('state') == 'aprobado':
            candidatos_aprobar = self.filtered(lambda r: r.state != 'aprobado').ids

        if vals.get('manual_file') and not vals.get('state'):
            candidatos_reemplazar = self.filtered(lambda r: r.url_nextcloud).ids

        result = super().write(vals)

        for rec in self.browse(candidatos_aprobar).exists():
            filename = rec.manual_filename or ''
            if rec.manual_file and filename and '_' in filename:
                rec._subir_manual_a_nextcloud(es_reemplazo=False)
            else:
                motivos = []
                if not rec.manual_file:
                    motivos.append('sin archivo PDF adjunto')
                if not filename or '_' not in filename:
                    motivos.append(
                        'el nombre "%s" no tiene el formato CODIGO_NOMBRE.pdf' % filename
                    )
                rec.message_post(
                    body='<p><b>Nextcloud:</b> Manual no subido automaticamente: %s.</p>'
                         % ', '.join(motivos)
                )

        for rec in self.browse(candidatos_reemplazar).exists():
            filename = rec.manual_filename or ''
            if rec.manual_file and filename and '_' in filename:
                rec._subir_manual_a_nextcloud(es_reemplazo=True)
            else:
                motivos = []
                if not rec.manual_file:
                    motivos.append('sin archivo PDF adjunto')
                if not filename or '_' not in filename:
                    motivos.append(
                        'el nombre "%s" no tiene el formato CODIGO_NOMBRE.pdf' % filename
                    )
                rec.message_post(
                    body='<p><b>Nextcloud:</b> Reemplazo no procesado: %s.</p>'
                         % ', '.join(motivos)
                )

        return result

    def _subir_manual_a_nextcloud(self, es_reemplazo=False):
        """Sube manual_file a Nextcloud y limpia el binario de Odoo."""
        self.ensure_one()
        try:
            import requests
            from requests.auth import HTTPBasicAuth

            ICP = self.env['ir.config_parameter'].sudo()
            nc_url    = (ICP.get_param('nextcloud.manuales.url') or '').rstrip('/')
            nc_user   = ICP.get_param('nextcloud.manuales.user') or ''
            nc_pass   = ICP.get_param('nextcloud.manuales.password') or ''
            nc_folder = (
                ICP.get_param('nextcloud.manuales.folder') or 'Drive-Migration/Manuales'
            ).strip('/')
            share_url = (ICP.get_param('nextcloud.manuales.share_url') or '').rstrip('/')

            if not nc_url or not nc_user or not nc_pass:
                self.message_post(
                    body='<p><b>Nextcloud:</b> Faltan parametros del sistema. '
                         'Pide a desarrollo que los configure.</p>'
                )
                return

            content = base64.b64decode(self.manual_file)
            filename = self.manual_filename
            upload_url = '{}/remote.php/dav/files/{}/{}/{}'.format(
                nc_url, nc_user, nc_folder, filename
            )

            resp = requests.put(
                upload_url,
                data=content,
                auth=HTTPBasicAuth(nc_user, nc_pass),
                timeout=30,
            )

            if resp.status_code in (200, 201, 204):
                file_url = (
                    '{}/download?path=%2F&files={}'.format(share_url, quote(filename))
                    if share_url else upload_url
                )
                self._limpiar_manual_binario(file_url)
                if es_reemplazo:
                    self._resetear_a_por_aprobar()
                self.message_post(
                    body='<p><b>Nextcloud [OK]:</b> Manual subido y PDF liberado de Odoo. '
                         '<a href="%s" target="_blank">Ver manual en Nextcloud</a>.</p>'
                         % file_url
                )
                _logger.info(
                    'amunet_manuales_nextcloud: subido %s → HTTP %s; binario liberado',
                    filename, resp.status_code,
                )
            else:
                self.message_post(
                    body='<p><b>Nextcloud [Error]:</b> No se pudo subir <b>%s</b>. '
                         'HTTP %s. Contacta a desarrollo.</p>' % (filename, resp.status_code)
                )

        except Exception as exc:
            _logger.exception(
                'amunet_manuales_nextcloud: excepcion al subir %s', self.manual_filename
            )
            self.message_post(
                body='<p><b>Nextcloud [Error]:</b> %s. Contacta a desarrollo.</p>' % str(exc)
            )

    def _resetear_a_por_aprobar(self):
        """Regresa el manual a 'por_aprobar' cuando se sube una nueva versión del PDF."""
        self.ensure_one()
        self.env.cr.execute(
            "UPDATE amunet_doc_compartida SET state = 'por_aprobar', write_date = NOW() WHERE id = %s",
            [self.id],
        )
        self.invalidate_recordset(['state'])
        calidad = self._usuarios_calidad()
        self.message_post(
            body='<p>Se subió una nueva versión del PDF a Nextcloud. '
                 'El manual queda <b>listo para aprobar</b>; Calidad debe revisar la nueva versión.</p>',
            message_type='notification',
            subtype_xmlid='mail.mt_note',
            partner_ids=calidad.mapped('partner_id').ids,
        )

    @api.model
    def _cron_recordatorio_calidad(self):
        """Cada 2 horas: notifica en Odoo a Calidad sobre manuales pendientes de aprobación."""
        pendientes = self.search([('state', '=', 'por_aprobar')])
        if not pendientes:
            return
        ahora = fields.Datetime.now()
        for rec in pendientes:
            delta = ahora - (rec.write_date or ahora)
            horas = int(delta.total_seconds() // 3600)
            mins = int((delta.total_seconds() % 3600) // 60)
            tiempo = '%dh %dmin' % (horas, mins) if horas else '%d min' % mins
            calidad = rec._usuarios_calidad() - rec._usuarios_validacion()
            if not calidad:
                continue
            rec.message_post(
                body='<p>⏰ <b>Recordatorio:</b> Este manual lleva <b>%s</b> '
                     'esperando aprobación de Calidad.</p>' % tiempo,
                message_type='notification',
                subtype_xmlid='mail.mt_note',
                partner_ids=calidad.mapped('partner_id').ids,
            )

    def _limpiar_manual_binario(self, url):
        """Elimina el binario PDF de Odoo y guarda el enlace a Nextcloud.
        Conserva manual_filename para que el link siga mostrando el nombre del archivo."""
        self.ensure_one()
        self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'amunet.doc.compartida'),
            ('res_id', '=', self.id),
            ('res_field', '=', 'manual_file'),
        ]).unlink()
        self.env.cr.execute(
            "UPDATE amunet_doc_compartida SET url_nextcloud = %s, write_date = NOW() WHERE id = %s",
            [url, self.id],
        )
        self.invalidate_recordset(['manual_file', 'url_nextcloud', 'enlace_pdf'])
