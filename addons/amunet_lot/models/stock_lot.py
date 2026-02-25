# -*- coding: utf-8 -*-
from odoo import models, fields


class StockLot(models.Model):
    _inherit = 'stock.lot'
    
    # Campo para indicar si el lote fue generado automáticamente
    amunet_auto_generated = fields.Boolean(
        string='Generado automáticamente',
        default=False,
        readonly=True,
        help="Indica si este lote fue generado automáticamente por el sistema"
    )
    
    # Relación con lote de fábrica
    factory_lot_id = fields.Many2one(
        'amunet.lot.factory',
        string='Número de serie/lote de fábrica',
        index=True,
        ondelete='restrict',
        help='Número de serie/lote de fábrica asociado a este Número de serie/lote de Amunet'
    )

    # Campo manufacturing_date - Sincronizado desde la línea
    manufacturing_date = fields.Date(
        string='Fecha de fabricación',
        help='Fecha de fabricación del lote, sincronizada desde el movimiento de inventario.',
        tracking=True,
    )

