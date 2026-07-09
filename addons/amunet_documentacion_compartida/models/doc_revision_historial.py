from odoo import models, fields, api

CAMPOS_LABEL = {
    'rev_materiales': 'Precauciones',
    'rev_volumenes': 'Volúmenes de reactivos',
    'rev_tiempos': 'Tiempos de interpretación',
    'rev_adicional': 'Adicional',
}


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
        ('cambio_criterio', '✏️ Cambio de criterio'),
    ], string='Acción', required=True)
    fecha = fields.Datetime(
        string='Fecha', default=fields.Datetime.now, readonly=True)

    # Campos para cambios de criterio
    campo = fields.Char(string='Criterio (técnico)')
    campo_label = fields.Char(
        string='Criterio', compute='_compute_campo_label', store=True)
    valor_anterior = fields.Selection(
        [('ok', '✓ Correcto'), ('fail', '✗ Incorrecto')],
        string='Antes')
    valor_nuevo = fields.Selection(
        [('ok', '✓ Correcto'), ('fail', '✗ Incorrecto')],
        string='Después')
    motivo = fields.Text(string='Motivo')

    @api.depends('campo')
    def _compute_campo_label(self):
        for rec in self:
            rec.campo_label = CAMPOS_LABEL.get(rec.campo, rec.campo or '')
