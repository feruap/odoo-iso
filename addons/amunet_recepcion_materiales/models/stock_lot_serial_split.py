# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockLotSerialSplit(models.Model):
    _inherit = 'stock.lot'

    # Lote del que se originó esta separación (solo se llena en lotes derivados)
    amunet_source_lot_id = fields.Many2one(
        'stock.lot', string='Lote origen (separación)',
        index=True, ondelete='set null',
    )
    # Lista de seriales como texto para mostrar en la recepción
    amunet_serial_list = fields.Char(
        compute='_compute_amunet_serial_list',
        string='Seriales',
    )

    @api.depends('amunet_serial_ids.serial_number')
    def _compute_amunet_serial_list(self):
        for lot in self:
            serials = lot.amunet_serial_ids.sorted('serial_number').mapped('serial_number')
            lot.amunet_serial_list = ', '.join(serials) if serials else '—'

    def action_open_serial_split_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Separar seriales defectuosos',
            'res_model': 'amunet.lot.serial.split.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_lot_id': self.id},
        }


class StockMoveLineSerials(models.Model):
    _inherit = 'stock.move.line'

    amunet_serial_list = fields.Char(
        related='lot_id.amunet_serial_list',
        string='Números de serie',
        store=False,
    )
