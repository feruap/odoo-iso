# -*- coding: utf-8 -*-
from odoo import api, models, _


class StockReorderNotify(models.Model):
    _inherit = 'stock.warehouse.orderpoint'
    _description = 'Reorder point with min/max notifications'

    def _amunet_mp_stock_split(self, product):
        """Devuelve (fabrica, burgos) del producto en los almacenes de
        Materia Prima: AMP (Fabrica) y AMPB (Burgos), sumando sus
        ubicaciones internas. El minimo se evalua contra el TOTAL de ambos."""
        Quant = self.env['stock.quant'].sudo()
        quants = Quant.search([
            ('product_id', '=', product.id),
            ('location_id.usage', '=', 'internal'),
        ])
        fabrica = 0.0
        burgos = 0.0
        for q in quants:
            name = q.location_id.complete_name or ''
            if name.startswith('AMP/'):
                fabrica += q.quantity
            elif name.startswith('AMPB/'):
                burgos += q.quantity
        return fabrica, burgos

    def _amunet_classify_minimos(self):
        """Clasifica los orderpoints activos considerando el stock TOTAL de
        Materia Prima (Fabrica + Burgos). Devuelve dos listas de dicts:
          - comprar:   el total (Fabrica+Burgos) esta bajo el minimo.
          - trasladar: Fabrica esta bajo el minimo pero el total alcanza
                       (hay en Burgos para mover a Fabrica).
        El minimo (product_min_qty) es el total deseado entre ambos almacenes.
        """
        comprar, trasladar = [], []
        orderpoints = self.env['stock.warehouse.orderpoint'].sudo().search([
            ('active', '=', True),
        ])
        # Un producto puede tener varias reglas (una por almacen); lo
        # evaluamos una sola vez por producto para no duplicar.
        vistos = set()
        for op in orderpoints:
            mn = op.product_min_qty
            if mn <= 0 or op.product_id.id in vistos:
                continue
            vistos.add(op.product_id.id)
            fabrica, burgos = self._amunet_mp_stock_split(op.product_id)
            total = fabrica + burgos
            if total < mn:
                comprar.append({
                    'product': op.product_id, 'min': mn,
                    'fabrica': fabrica, 'burgos': burgos, 'total': total,
                    'faltan': mn - total,
                })
            elif fabrica < mn:
                trasladar.append({
                    'product': op.product_id, 'min': mn,
                    'fabrica': fabrica, 'burgos': burgos, 'total': total,
                    'mover': min(mn - fabrica, burgos),
                })
        return comprar, trasladar

    def _amunet_notify_minimos(self, user_ids=None):
        """Notifica materia prima bajo minimo distinguiendo COMPRAR (total
        Fabrica+Burgos bajo el minimo) de TRASLADAR (Fabrica corta pero hay
        en Burgos)."""
        comprar, trasladar = self._amunet_classify_minimos()
        if not comprar and not trasladar:
            return

        if user_ids is None:
            user_ids = [78]

        partes = []
        if comprar:
            filas = [
                f'• {d["product"].display_name}: total {d["total"]:.0f} '
                f'(Fábrica {d["fabrica"]:.0f} + Burgos {d["burgos"]:.0f}), '
                f'mínimo {d["min"]:.0f} — faltan {d["faltan"]:.0f}.'
                for d in comprar
            ]
            partes.append(
                '<b>COMPRAR</b> (el total Fábrica+Burgos está bajo el '
                'mínimo):<br/>' + '<br/>'.join(filas))
        if trasladar:
            filas = [
                f'• {d["product"].display_name}: Fábrica {d["fabrica"]:.0f} '
                f'(mínimo {d["min"]:.0f}), Burgos {d["burgos"]:.0f} — '
                f'trasladar ~{d["mover"]:.0f} de Burgos a Fábrica.'
                for d in trasladar
            ]
            partes.append(
                '<b>TRASLADAR DE BURGOS A FÁBRICA</b> (Fábrica corta, pero '
                'hay existencia en Burgos):<br/>' + '<br/>'.join(filas))

        cuerpo = ('<br/><br/>'.join(partes)
                  + '<br/><br/>El mínimo es el total deseado entre los dos '
                    'almacenes de Materia Prima (Fábrica + Burgos).')

        users = self.env['res.users'].browse(user_ids)
        partner_ids = users.mapped('partner_id').ids
        self.env['res.partner'].browse(partner_ids).message_notify(
            subject=_('Materia Prima bajo mínimo — comprar / trasladar'),
            body=cuerpo,
            partner_ids=partner_ids,
        )
