# -*- coding: utf-8 -*-
from odoo import models, fields


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    factory_lot_id = fields.Many2one(
        'amunet.lot.factory',
        string='Número de serie/lote de fábrica',
        related='lot_id.factory_lot_id',
        store=True,
        readonly=True,
        help='Número de serie/lote de fábrica asociado al lote Amunet'
    )
