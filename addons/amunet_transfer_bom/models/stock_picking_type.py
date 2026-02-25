# -*- coding: utf-8 -*-

from odoo import models, fields


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    enable_bom_transfer = fields.Boolean(
        string='Habilitar entrega por lista de materiales',
        default=False,
        help='Permite usar listas de materiales para agregar componentes automáticamente en entregas'
    )
