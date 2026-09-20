from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    amunet_solicitud_compra_id = fields.Many2one(
        'amunet.solicitud.compra',
        string='Solicitud de compra',
        readonly=True, copy=False, index=True,
        help='Solicitud que origino esta recepcion al autorizarse.',
    )
