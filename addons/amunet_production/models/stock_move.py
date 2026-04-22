from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    amunet_is_valid = fields.Boolean(
        string='Válido',
        default=False,
        tracking=True,
        help='Validación técnica manual del ingrediente/reactivo antes de usarse en la solución.'
    )

    amunet_dissolution = fields.Char(string='Disolución')
    amunet_ph_adjustment = fields.Char(string='Ajuste de pH')
    amunet_lot_id = fields.Many2one('stock.lot', string='Lote')
