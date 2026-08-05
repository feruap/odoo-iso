from odoo import models, fields


class StockScrapAmunet(models.Model):
    _inherit = 'stock.scrap'

    amunet_fecha_caducidad = fields.Datetime(
        related='lot_id.expiration_date',
        string='Fecha de caducidad',
        readonly=True,
        store=False,
    )
