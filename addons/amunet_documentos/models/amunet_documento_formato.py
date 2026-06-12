# -*- coding: utf-8 -*-
from odoo import fields, models
from . import amunet_documento as _doc_module


class AmunetDocumentoFormato(models.Model):
    _name = 'amunet.documento.formato'
    _description = 'Formato derivado descargable'
    _order = 'sequence, id'

    documento_id = fields.Many2one(
        'amunet.documento', string='Documento', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    codigo = fields.Char(string='Código', required=True)
    nombre = fields.Char(string='Nombre del formato', required=True)
    archivo = fields.Binary(string='Archivo', attachment=True)
    archivo_filename = fields.Char(string='Nombre de archivo')
    doc_area = fields.Selection(
        related='documento_id.area', string='Área', store=True)
    doc_codigo = fields.Char(
        related='documento_id.codigo', string='Código PNO', store=False)
    requiere_aprobacion = fields.Boolean(
        string='Requiere aprobación para descargar', default=False)

    def action_solicitar_descarga(self):
        Solicitud = self.env['amunet.documento.formato.solicitud']
        existente = Solicitud.search([
            ('formato_id', '=', self.id),
            ('solicitante_id', '=', self.env.user.id),
            ('state', 'in', ('pendiente', 'aprobada')),
        ], limit=1)
        if not existente:
            existente = Solicitud.create({'formato_id': self.id})
            self._avisar_documentacion(existente)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mi solicitud de descarga',
            'res_model': 'amunet.documento.formato.solicitud',
            'res_id': existente.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _avisar_documentacion(self, solicitud):
        self.env['mail.mail'].sudo().create({
            'subject': f'📥 Solicitud de descarga: {self.codigo} — {solicitud.solicitante_id.name}',
            'body_html': f'''
                <p>Nueva solicitud de descarga pendiente de aprobación:</p>
                <ul>
                    <li><b>Formato:</b> {self.codigo} — {self.nombre}</li>
                    <li><b>Documento:</b> {self.documento_id.codigo}</li>
                    <li><b>Solicitante:</b> {solicitud.solicitante_id.name}</li>
                </ul>
                <p>Revísala en Odoo: <b>Documentación → Solicitudes de descarga</b></p>
            ''',
            'email_to': 'documentacion@amunet.com.mx',
        }).send()

    def _check_editable(self, vals=None):
        _doc_module._check_documento_child_editable(self, vals)

    def write(self, vals):
        self._check_editable(vals)
        return super().write(vals)

    def unlink(self):
        self._check_editable()
        return super().unlink()
