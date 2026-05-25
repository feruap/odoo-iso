# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    amunet_serial_ids = fields.One2many(
        'amunet.equipment.serial',
        'lot_id',
        string='Series del equipo',
    )
    amunet_serial_count = fields.Integer(
        compute='_compute_amunet_serial_count',
        string='# Series',
    )
    amunet_allow_multi_serial = fields.Boolean(
        related='product_id.product_tmpl_id.amunet_allow_multi_serial',
        string='Permite multiples series',
        store=False,
    )

    @api.depends('amunet_serial_ids')
    def _compute_amunet_serial_count(self):
        for rec in self:
            rec.amunet_serial_count = len(rec.amunet_serial_ids)
