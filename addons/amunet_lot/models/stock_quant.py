# -*- coding: utf-8 -*-
from odoo import models, fields


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    factory_lot_id = fields.Many2one(
        'amunet.lot.factory',
        string='Número de serie/lote de fábrica',
        related='lot_id.factory_lot_id',
        store=True,
        readonly=True,
        help='Lote de fábrica asociado al lote Amunet de este quant'
    )
