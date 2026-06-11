# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api, _
from odoo.exceptions import UserError


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
        copy=False,
    )

    amunet_qty_used = fields.Float(
        string='Cantidad utilizada',
        digits='Product Unit of Measure',
        copy=False,
        help='Cantidad real consumida en producción. Se captura durante la conciliación.',
    )

    amunet_qty_surplus = fields.Float(
        string='Sobrante',
        compute='_compute_amunet_qty_surplus',
        digits='Product Unit of Measure',
        store=False,
    )

    @api.depends('amunet_qty_supplied', 'amunet_qty_used')
    def _compute_amunet_qty_surplus(self):
        for move in self:
            surplus = (move.amunet_qty_supplied or 0.0) - (move.amunet_qty_used or 0.0)
            move.amunet_qty_surplus = max(surplus, 0.0)

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

    # Flag de UI: True si el usuario actual es de Almacen. Solo almacen
    # (Veronica, Patricia, Karla...) puede capturar Cantidad surtida y Lote.
    amunet_user_is_warehouse = fields.Boolean(
        string='Es de almacen',
        compute='_compute_amunet_user_is_warehouse',
    )

    @api.depends_context('uid')
    def _compute_amunet_user_is_warehouse(self):
        is_wh = (
            self.env.user.has_group('amunet_material_request.group_material_warehouse')
            or self.env.user.has_group('amunet_material_request.group_material_manager')
        )
        for rec in self:
            rec.amunet_user_is_warehouse = is_wh

    def write(self, vals):
        # Candado: solo Almacen puede capturar 'Cantidad surtida' y 'Lote'
        # del material de una orden de produccion. Produccion nunca.
        # Se omite en escrituras internas del flujo (contexto/sudo).
        supply_fields = {'amunet_qty_supplied', 'amunet_lot_id'}
        if (supply_fields & set(vals)
                and not self.env.su
                and not self.env.context.get('amunet_supply_internal')):
            is_wh = (
                self.env.user.has_group('amunet_material_request.group_material_warehouse')
                or self.env.user.has_group('amunet_material_request.group_material_manager')
            )
            if not is_wh and any(m.raw_material_production_id for m in self):
                raise UserError(_(
                    'Solo personal de Almacen (Veronica, Patricia, Karla) puede '
                    'capturar la Cantidad surtida y el Lote del material.'))
        # Candado: la 'Cantidad por consumir' (product_uom_qty) de un
        # componente NO se puede ajustar una vez que la orden esta
        # planificada (confirmada en adelante). Por nadie. Se omite en
        # escrituras internas del flujo (sudo/contexto).
        if ('product_uom_qty' in vals
                and not self.env.su
                and not self.env.context.get('amunet_supply_internal')):
            for m in self:
                mo = m.raw_material_production_id
                if mo and mo.state != 'draft':
                    raise UserError(_(
                        'No se puede ajustar la cantidad por consumir: la orden '
                        '%s ya esta planificada.') % mo.name)
        return super().write(vals)

    amunet_is_valid = fields.Boolean(
        string='Valido',
        compute='_compute_amunet_is_valid',
        store=True,
        help='Automatico: cantidad dentro del rango de pesaje y disolucion confirmada si aplica.'
    )

    @api.depends('quantity', 'product_uom_qty', 'product_id', 'amunet_dissolution', 'raw_material_production_id.product_id.categ_id')
    def _compute_amunet_is_valid(self):
        for move in self:
            qty_used = move.quantity
            product = move.product_id

            if not qty_used or qty_used <= 0:
                move.amunet_is_valid = False
                continue

            # Detectar si la MO es de tipo Solucion (categoria del
            # producto a fabricar contiene 'solucion'). Solo en ese
            # flujo aplican los checks estrictos de rango de pesaje y
            # disolucion. Para kits y otros productos, basta con que
            # la cantidad utilizada sea > 0.
            mo_product = move.raw_material_production_id.product_id
            categ = mo_product.categ_id if mo_product else False
            categ_name = (categ.complete_name or categ.name or '') if categ else ''
            es_solucion = 'solucion' in categ_name.lower()

            if not es_solucion:
                # Kit / otro: validez = cantidad utilizada positiva
                move.amunet_is_valid = True
                continue

            # Flujo Solucion: check de rango de pesaje + disolucion
            qty_required = move.product_uom_qty
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

            if not move.amunet_dissolution:
                move.amunet_is_valid = False
                continue

            move.amunet_is_valid = in_range

    def _action_done(self, cancel_backorder=False):
        """Gate SGC de salida: bloquea movimientos que sacan un lote
        fuera del inventario interno (a customer/transit) si el lote
        fue producido por una MO que aun no tiene QC aprobado.

        Aplica solo cuando el producto requiere control de calidad
        (qc_required = True). Para productos sin QC, no afecta.

        ISO 13485 / Cofepris: producto NO se libera al mercado sin
        autorizacion de QC.
        """
        for move in self:
            if move.location_id.usage != 'internal':
                continue
            if move.location_dest_id.usage not in ('customer', 'transit'):
                continue
            for ml in move.move_line_ids:
                if not ml.lot_id or ml.quantity <= 0:
                    continue
                product = ml.product_id or move.product_id
                if not product.product_tmpl_id.qc_required:
                    continue
                # Buscar la MO que produjo este lote (a traves de
                # lot_producing_ids; usa 'in' porque es Many2many).
                mo = self.env['mrp.production'].sudo().search([
                    ('lot_producing_ids', 'in', ml.lot_id.id),
                ], limit=1)
                if mo and mo.quality_analysis_status != 'approved':
                    raise UserError(_(
                        'No se puede liberar el lote %(lot)s del producto '
                        '%(prod)s. El analisis de calidad del MO %(mo)s '
                        'esta en estado "%(qc)s", no esta aprobado todavia. '
                        'Espera la aprobacion de QC antes de sacar el '
                        'producto del inventario interno.'
                    ) % {
                        'lot': ml.lot_id.name,
                        'prod': product.display_name,
                        'mo': mo.name,
                        'qc': dict(mo._fields['quality_analysis_status'].selection).get(
                            mo.quality_analysis_status, mo.quality_analysis_status
                        ),
                    })
        return super()._action_done(cancel_backorder=cancel_backorder)
