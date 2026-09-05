# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    """Orden de fabricación: origen de la ENTREGA de material al almacén.

    Por convención de Amunet la orden de fabricación ES el lote (la orden
    ``0826/01/PSS`` produce el lote ``0826/01/PSS``), así que la entrega se
    registra desde aquí y de la orden salen producto, lote y caducidad sin
    recapturarlos a mano.

    Cambio de diseño (ENTREGA/RECEPCIÓN-céntrico): al cerrar la MO ya NO se
    publica nada a la tienda. El producto terminado espera a que Acondicionado
    lo ENTREGUE y el almacén lo RECIBA; solo entonces, y si es vendible, se
    publica. Por eso no se sobreescribe ``button_mark_done``: no debe
    interferir con el cierre de producción ni publicar existencias que el
    almacén todavía no ha recibido.
    """

    _inherit = "mrp.production"

    def _amunet_woo_entrega(self, tipo):
        """Registra la entrega de esta orden al almacén de venta."""
        self.ensure_one()
        if not self.env.user.has_group(
                'amunet_woocommerce.group_woo_acondicionado'):
            raise UserError(_(
                'Solo el personal de Acondicionado puede registrar la entrega '
                'de material al almacén de producto terminado.'))
        Delivery = self.env['amunet.woo.delivery']
        delivery = Delivery._crear_desde_produccion(self, tipo)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Entrega de material'),
            'res_model': 'amunet.woo.delivery',
            'res_id': delivery.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_amunet_entrega_completa(self):
        """Entrega TODO lo que queda pendiente del lote."""
        return self._amunet_woo_entrega('completa')

    def action_amunet_entrega_parcial(self):
        """Abre una entrega PARCIAL para capturar la cantidad entregada."""
        self.ensure_one()
        if not self.env.user.has_group(
                'amunet_woocommerce.group_woo_acondicionado'):
            raise UserError(_(
                'Solo el personal de Acondicionado puede registrar la entrega '
                'de material al almacén de producto terminado.'))
        Delivery = self.env['amunet.woo.delivery']
        lot = Delivery._resolve_lot_from_production(self)
        if not lot:
            raise UserError(_(
                'La orden %s todavía no tiene lote de producto terminado. '
                'Producción debe registrar el lote antes de entregarlo.')
                % self.name)
        pendiente = Delivery._pending_qty_for_lot(lot)
        if pendiente <= 0:
            raise UserError(_(
                'El lote %s no tiene piezas pendientes por entregar en el '
                'almacén de piezas de APT.') % lot.name)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Entrega parcial de material'),
            'res_model': 'amunet.woo.delivery',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_production_id': self.id,
                'default_product_id': self.product_id.id,
                'default_lot_id': lot.id,
                'default_tipo': 'parcial',
                'default_quantity_delivered': pendiente,
            },
        }
