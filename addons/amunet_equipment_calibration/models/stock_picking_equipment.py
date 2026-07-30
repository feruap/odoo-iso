# -*- coding: utf-8 -*-
from odoo import models

# Código del producto genérico no-inventariable-por-clave usado para el
# ingreso de equipos de uso interno. Se crea una sola vez (script).
CODIGO_PRODUCTO_EQUIPO = 'EQUIPO-USO-INTERNO'


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super().button_validate()
        # Solo actuar cuando la recepción realmente quedó hecha.
        for pick in self.filtered(lambda p: p.state == 'done'):
            pick._amunet_crear_solicitudes_equipo()
        return res

    def _amunet_crear_solicitudes_equipo(self):
        self.ensure_one()
        if self.picking_type_id.code != 'incoming':
            return
        generic = self.env['product.product'].search(
            [('default_code', '=', CODIGO_PRODUCTO_EQUIPO)], limit=1)
        if not generic:
            return
        moves = self.move_ids.filtered(
            lambda m: m.product_id == generic and m.state == 'done'
            and (m.quantity or 0) > 0)
        if not moves:
            return
        Req = self.env['amunet.equipment.request'].sudo()
        for mv in moves:
            # La serie del equipo se captura en "Serie / Lote proveedor".
            serie = mv.amunet_supplier_lot or ''
            # Evitar duplicar si ya existe solicitud para esta recepción+serie.
            if Req.search_count([('picking_id', '=', self.id),
                                 ('serie_recibida', '=', serie)]):
                continue
            dest = (mv.move_line_ids[:1].location_dest_id or mv.location_dest_id)
            Req.create({
                'picking_id': self.id,
                'product_id': generic.id,
                'serie_recibida': serie,
                'fecha_recepcion': self.date_done or self.scheduled_date,
                'partner_id': self.partner_id.id if self.partner_id else False,
                'location_id': dest.id,
            })
