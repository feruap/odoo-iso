from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _amunet_anaquel_pt(self):
        param = self.env['ir.config_parameter'].sudo().get_param(
            'amunet.distribucion.location_pt')
        try:
            loc_id = int(param) if param else 14
        except (TypeError, ValueError):
            loc_id = 14
        return self.env['stock.location'].browse(loc_id)

    def _action_done(self, cancel_backorder=False):
        moves = super()._action_done(cancel_backorder=cancel_backorder)
        anaquel = moves._amunet_anaquel_pt() if moves else False
        if not anaquel or not anaquel.exists():
            return moves
        Traspaso = self.env['amunet.traspaso.distribucion'].sudo()
        for move in moves.filtered(lambda m: m.state == 'done'):
            # Solo ingresos: lo que sale del anaquel no se vuelve a solicitar.
            if move.location_dest_id != anaquel or move.location_id == anaquel:
                continue
            for line in move.move_line_ids:
                if line.quantity <= 0:
                    continue
                Traspaso.create({
                    'product_id': line.product_id.id,
                    'lot_id': line.lot_id.id or False,
                    'quantity': line.quantity,
                    'uom_id': line.product_uom_id.id,
                    'origin_move_id': move.id,
                    'origin': move.picking_id.name or move.reference or '',
                    'location_id': anaquel.id,
                })
        return moves
