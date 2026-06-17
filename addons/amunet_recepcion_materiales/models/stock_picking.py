# -*- coding: utf-8 -*-
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_confirm(self):
        # Para recepciones entrantes: generar lote Amunet automáticamente
        # ANTES de que action_confirm cree las move_lines, para que las hereden
        for picking in self.filtered(lambda p: p.picking_type_code == 'incoming'):
            for move in picking.move_ids.filtered(
                lambda m: m.product_id.tracking in ('lot', 'serial')
                and m.product_id.lot_sequence_id
                and not m.lot_ids
            ):
                lot_name = move.product_id.lot_sequence_id.next_by_id()
                lot = self.env['stock.lot'].search([
                    ('name', '=', lot_name),
                    ('product_id', '=', move.product_id.id),
                ], limit=1)
                if not lot:
                    lot = self.env['stock.lot'].sudo().create({
                        'name': lot_name,
                        'product_id': move.product_id.id,
                        'company_id': move.company_id.id,
                    })
                move.lot_ids = [(4, lot.id)]
        return super().action_confirm()
