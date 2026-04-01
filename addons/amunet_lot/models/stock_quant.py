# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    # factory_lot_id - Vinculado al lote, editable para lotes nuevos via vista
    factory_lot_id = fields.Many2one(
        'amunet.lot.factory',
        string='Número de serie/lote de fábrica',
        related='lot_id.factory_lot_id',
        store=True,
        readonly=False,
        help='Lote de fábrica asociado al lote Amunet de este quant'
    )

    analysis_number = fields.Char(
        related='lot_id.analysis_number',
        string='No. Análisis',
        readonly=False,
    )

    manufacturing_date = fields.Date(
        related='lot_id.manufacturing_date',
        string='Fecha de fabricación',
        readonly=False,
    )

    expiration_date = fields.Datetime(
        related='lot_id.expiration_date',
        string='Fecha de caducidad',
        readonly=False,
    )

    removal_date = fields.Datetime(
        related='lot_id.removal_date',
        string='Fecha de remoción',
        readonly=False,
    )

    @api.model
    def _get_inventory_fields_write(self):
        """ Allow traceability fields to be written during physical inventory routing. """
        fields = super()._get_inventory_fields_write()
        return fields + [
            'analysis_number',
            'factory_lot_id',
            'manufacturing_date',
            'expiration_date',
            'removal_date'
        ]
