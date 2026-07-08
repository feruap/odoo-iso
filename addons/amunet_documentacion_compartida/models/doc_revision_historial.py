from odoo import models, fields


class DocRevisionHistorial(models.Model):
    _name = 'amunet.doc.revision.historial'
    _description = 'Historial de revisiones'
    _order = 'fecha desc'

    doc_id = fields.Many2one(
        'amunet.doc.compartida', required=True, ondelete='cascade')
    usuario_id = fields.Many2one(
        'res.users', string='Usuario', required=True)
    accion = fields.Selection([
        ('cierre', '✓ Revisión cerrada'),
        ('reapertura', '🔄 Reapertura'),
    ], string='Acción', required=True)
    fecha = fields.Datetime(
        string='Fecha', default=fields.Datetime.now, readonly=True)
