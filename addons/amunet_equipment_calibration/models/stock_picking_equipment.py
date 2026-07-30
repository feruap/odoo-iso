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
        lineas = self.move_line_ids.filtered(
            lambda l: l.product_id == generic and l.quantity > 0)
        if not lineas:
            return
        Req = self.env['amunet.equipment.request'].sudo()
        for ml in lineas:
            lot = ml.lot_id
            # Evitar duplicar si ya existe solicitud para esta recepción+serie.
            dominio = [('picking_id', '=', self.id)]
            if lot:
                dominio.append(('lot_id', '=', lot.id))
            else:
                dominio.append(('serie_recibida', '=', ml.lot_name or ''))
            if Req.search_count(dominio):
                continue
            Req.create({
                'picking_id': self.id,
                'product_id': generic.id,
                'lot_id': lot.id if lot else False,
                'serie_recibida': lot.name if lot else (ml.lot_name or ''),
                'fecha_recepcion': self.date_done or self.scheduled_date,
                'partner_id': self.partner_id.id if self.partner_id else False,
                'location_id': ml.location_dest_id.id,
            })
