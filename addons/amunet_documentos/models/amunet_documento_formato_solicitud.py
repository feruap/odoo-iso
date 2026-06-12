# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AmunetDocumentoFormatoSolicitud(models.Model):
    _name = 'amunet.documento.formato.solicitud'
    _description = 'Solicitud de impresión de formato controlado'
    _order = 'fecha_solicitud desc'
    _inherit = ['mail.thread']

    formato_id = fields.Many2one(
        'amunet.documento.formato', string='Formato',
        required=True, ondelete='cascade')
    documento_id = fields.Many2one(
        related='formato_id.documento_id', store=True, string='Documento')
    formato_codigo = fields.Char(
        related='formato_id.codigo', store=True, string='Código')
    formato_nombre = fields.Char(
        related='formato_id.nombre', store=True, string='Formato')
    archivo = fields.Binary(
        related='formato_id.archivo', string='Archivo', readonly=True)
    archivo_filename = fields.Char(
        related='formato_id.archivo_filename', readonly=True)

    solicitante_id = fields.Many2one(
        'res.users', string='Solicitante',
        default=lambda self: self.env.user, required=True, readonly=True)
    fecha_solicitud = fields.Datetime(
        string='Solicitado el', default=fields.Datetime.now, readonly=True)
    motivo = fields.Text(string='Motivo de uso')

    state = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ], string='Estado', default='pendiente', tracking=True)
    notas_respuesta = fields.Text(string='Comentario')
    aprobado_por_id = fields.Many2one(
        'res.users', string='Respondido por', readonly=True)
    fecha_respuesta = fields.Datetime(string='Fecha de respuesta', readonly=True)

    def action_aprobar(self):
        self.write({
            'state': 'aprobada',
            'aprobado_por_id': self.env.user.id,
            'fecha_respuesta': fields.Datetime.now(),
        })
        self._notificar_solicitante('aprobada')

    def action_rechazar(self):
        self.write({
            'state': 'rechazada',
            'aprobado_por_id': self.env.user.id,
            'fecha_respuesta': fields.Datetime.now(),
        })
        self._notificar_solicitante('rechazada')

    def _notificar_solicitante(self, estado):
        email = self.solicitante_id.email
        if not email:
            return
        icono = '✅' if estado == 'aprobada' else '❌'
        cuerpo = f'''
            <p>Hola {self.solicitante_id.name},</p>
            <p>Tu solicitud de impresión del formato
            <b>{self.formato_codigo} — {self.formato_nombre}</b>
            ({self.documento_id.codigo}) ha sido <b>{estado}</b>. {icono}</p>
        '''
        if self.notas_respuesta:
            cuerpo += f'<p><b>Comentario:</b> {self.notas_respuesta}</p>'
        if estado == 'aprobada':
            cuerpo += '<p>Ya puedes imprimir el archivo desde Odoo en <b>Documentación → Mis solicitudes de impresión</b>.</p>'
        self.env['mail.mail'].sudo().create({
            'subject': f'{icono} Solicitud de impresión {estado}: {self.formato_codigo}',
            'body_html': cuerpo,
            'email_to': email,
        }).send()
