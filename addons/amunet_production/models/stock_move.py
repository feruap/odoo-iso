# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    amunet_dissolution = fields.Boolean(string='Disolucion', default=False)
    amunet_ph_adjustment = fields.Char(string='Ajuste de pH')
    amunet_lot_id = fields.Many2one('stock.lot', string='Lote')

    # Cantidad que el almacen registra al surtir. Es distinta a
    # 'quantity' (cantidad utilizada/consumida nativa Odoo): esta la
    # captura almacen al entregar, 'quantity' la concilia produccion al
    # validar el surtido o cerrar la MO. Espeja qty_supplied de
    # amunet_material_request_line para mantener vocabulario.
    amunet_qty_supplied = fields.Float(
        string='Cantidad surtida',
        digits='Product Unit of Measure',
        tracking=True,
        copy=False,
    )

    # Flag de UI: True si el usuario actual puede editar la cantidad
    # teorica (product_uom_qty) y la utilizada (quantity). Almacen puro
    # NO debe modificarlas; solo produccion. Mery tiene ambos grupos en
    # staging asi que sigue pudiendo editar.
    amunet_user_can_edit_consume = fields.Boolean(
        string='Puede editar consumo',
        compute='_compute_amunet_user_can_edit_consume',
    )

    @api.depends_context('uid')
    def _compute_amunet_user_can_edit_consume(self):
        user = self.env.user
        can_edit = (
            user.has_group('amunet_production.group_production_supervisor')
            or user.has_group('amunet_production.group_production_operator')
            or user.has_group('mrp.group_mrp_user')
        )
        for rec in self:
            rec.amunet_user_can_edit_consume = can_edit

    amunet_is_valid = fields.Boolean(
        string='Valido',
        compute='_compute_amunet_is_valid',
        store=True,
        help='Automatico: cantidad dentro del rango de pesaje y disolucion confirmada si aplica.'
    )

    @api.depends('quantity', 'product_uom_qty', 'product_id', 'amunet_dissolution')
    def _compute_amunet_is_valid(self):
        for move in self:
            qty_used = move.quantity
            qty_required = move.product_uom_qty
            product = move.product_id

            if not qty_used or qty_used <= 0:
                move.amunet_is_valid = False
                continue

            # Parsear delta desde rango de pesaje del producto (formato: ± 0.0007)
            range_text = (product.product_tmpl_id.amunet_weighing_range_text or '') if product else ''
            delta = 0.0
            if range_text:
                match = re.search(r'[\d]+\.?[\d]*', range_text)
                if match:
                    try:
                        delta = float(match.group())
                    except ValueError:
                        delta = 0.0

            if delta > 0:
                in_range = (qty_required - delta) <= qty_used <= (qty_required + delta)
            else:
                in_range = qty_used > 0

            # La columna de disolucion funciona como un checklist, se requiere que este activada para validar
            if not move.amunet_dissolution:
                move.amunet_is_valid = False
                continue

            move.amunet_is_valid = in_range
