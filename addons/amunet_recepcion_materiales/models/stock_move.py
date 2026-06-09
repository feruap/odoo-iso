# -*- coding: utf-8 -*-
from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    amunet_supplier_lot = fields.Char('Lote del proveedor')
    amunet_mfg_date = fields.Date('Fecha de fabricación')
    amunet_exp_date = fields.Date('Fecha de caducidad')

    def _action_done(self, cancel_backorder=False):
        for move in self.filtered(
            lambda m: m.picking_type_id.code == 'incoming' and m.move_line_ids
            and (m.amunet_supplier_lot or m.amunet_mfg_date or m.amunet_exp_date)
        ):
            vals = {}
            if move.amunet_supplier_lot:
                factory_lot = self.env['amunet.lot.factory'].sudo().search(
                    [('name', '=', move.amunet_supplier_lot)], limit=1
                )
                if not factory_lot:
                    factory_lot = self.env['amunet.lot.factory'].sudo().create(
                        {'name': move.amunet_supplier_lot}
                    )
                vals['factory_lot_id'] = factory_lot.id
            if move.amunet_mfg_date:
                vals['manufacturing_date'] = move.amunet_mfg_date
            if move.amunet_exp_date:
                vals['expiration_date'] = move.amunet_exp_date
            move.move_line_ids.write(vals)
        return super()._action_done(cancel_backorder=cancel_backorder)
