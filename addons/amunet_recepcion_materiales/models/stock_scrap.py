from odoo import models, fields

MOTIVO_DEFAULT = 'Próximo a vencer'


class StockScrapAmunet(models.Model):
    _inherit = 'stock.scrap'

    amunet_motivo_descarte = fields.Char(
        string='Motivo de descarte',
        default=MOTIVO_DEFAULT,
    )
