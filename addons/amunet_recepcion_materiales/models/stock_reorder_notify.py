# -*- coding: utf-8 -*-
from odoo import api, models, _


class StockReorderNotify(models.Model):
    _inherit = 'stock.warehouse.orderpoint'
    _description = 'Reorder point with min/max notifications'

    def _amunet_notify_minimos(self, user_ids=None):
        """Revisa orderpoints bajo mínimo y notifica a los usuarios indicados."""
        bajo_minimo = self.env['stock.warehouse.orderpoint'].search([
            ('active', '=', True),
        ]).filtered(lambda op: op.qty_on_hand <= op.product_min_qty)

        if not bajo_minimo:
            return

        if user_ids is None:
            user_ids = [78]

        productos = []
        for op in bajo_minimo:
            productos.append(
                f'• {op.product_id.display_name}: '
                f'{op.qty_on_hand:.0f} en existencia (mínimo: {op.product_min_qty:.0f})'
            )

        cuerpo = (
            '<b>Los siguientes productos están en o por debajo de su mínimo de inventario:</b><br/>'
            + '<br/>'.join(productos)
            + '<br/><br/>Entra a <b>Inventario &gt; Reabastecimiento</b> para generar los pedidos.'
        )

        users = self.env['res.users'].browse(user_ids)
        partner_ids = users.mapped('partner_id').ids

        # Enviar notificación directa que aparece en la campana de Odoo
        self.env['res.partner'].browse(partner_ids).message_notify(
            subject=_('Productos bajo mínimo — revisar reabastecimiento'),
            body=cuerpo,
            partner_ids=partner_ids,
        )
