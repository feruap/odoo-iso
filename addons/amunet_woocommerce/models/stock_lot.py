# -*- coding: utf-8 -*-

import logging

from odoo import models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockLot(models.Model):
    """Recepción para venta de un lote LIBERADO por Calidad.

    Cambio de diseño (RECEPCIÓN-céntrico): la LIBERACIÓN por Calidad ya NO
    publica directamente a la tienda. Deja el lote "recibible"; la publicación
    la dispara la ACEPTACIÓN de la recepción por el almacén de venta (modelo
    ``amunet.woo.reception``). Se separan así las dos acciones, en orden:

        1) Calidad LIBERA el lote (paso regulatorio, ISO 13485 7.5.1).
        2) El almacén ACEPTA la recepción para venta (aquí) -> Woo disponible.

    Recibir material no liberado SÍ se permite (a veces urge): entra RETENIDO.
    El candado no está en recibir sino en PUBLICAR: solo sale a la tienda lo
    liberado por Calidad o lo autorizado bajo concesión (``amunet.woo.delivery``).
    """

    _inherit = "stock.lot"

    def write(self, vals):
        res = super().write(vals)
        # Al liberar, solo se avisa que el lote quedó recibible. NO se publica:
        # la publicación la dispara la aceptación de la recepción del almacén.
        if vals.get("amunet_lot_release_state") == "released":
            for lot in self:
                if "amunet_lot_release_state" not in lot._fields:
                    break
                if lot.amunet_lot_release_state == "released":
                    try:
                        lot.message_post(body=_(
                            "Lote LIBERADO por Calidad. Disponible para que el "
                            "almacén ACEPTE su recepción para venta."))
                    except Exception:  # noqa: BLE001 - nunca bloquear liberación
                        _logger.exception(
                            "Aviso de liberación de lote falló (ignorado)")
        return res

    def action_aceptar_recepcion_venta(self):
        """Recepción directa de un lote, SIN entrega previa de Acondicionado.

        Es la vía secundaria: la principal es que Acondicionado registre la
        entrega (``amunet.woo.delivery``) y el almacén la confirme. Esta queda
        para el material que llega sin entrega formal (p. ej. lotes históricos).

        Solo recibe lo que FALTA por recibir del lote (existencia libre en APT
        menos lo ya recibido). Antes tomaba toda la existencia en cada clic, de
        modo que tres clics "recibían" 795 pz de un lote de 265; ese era el
        error y por eso ahora se descuenta lo ya recibido.

        Recibir NO exige liberación de Calidad: el material entra RETENIDO y no
        se publica hasta que Calidad libere o se autorice bajo concesión.
        """
        Mapping = self.env['amunet.woo.product.mapping']
        Reception = self.env['amunet.woo.reception']
        created = Reception
        for lot in self:
            if not lot.product_id:
                raise UserError(_("El lote %s no tiene producto.") % lot.name)
            mapping = Mapping.search([
                ('relation_state', '=', 'confirmed'),
                ('product_id', '=', lot.product_id.id),
            ], limit=1)
            if not mapping:
                raise UserError(_(
                    "El producto %s no tiene un mapeo confirmado con la tienda; "
                    "no se puede recibir para venta todavía.")
                    % lot.product_id.display_name)
            # La configuracion de la tienda (ubicacion de piezas, credenciales)
            # esta reservada a administradores. El almacen NO tiene por que
            # verla para aceptar su recepcion: el sistema la lee por su cuenta
            # con sudo. Lo que si valida con los permisos del usuario es el
            # mapeo y la creacion de la recepcion.
            backend = mapping.backend_id.sudo()
            libre = backend._apt_released_qty_for_lot(lot)
            ya_recibido = sum(Reception.sudo().search([
                ('lot_id', '=', lot.id),
                ('state', '!=', 'cancelada'),
            ]).mapped('quantity'))
            qty = libre - ya_recibido
            if qty <= 0:
                raise UserError(_(
                    "El lote %(lot)s no tiene piezas pendientes por recibir: "
                    "hay %(hay)s en el almacén de piezas de APT y ya se "
                    "recibieron %(ya)s.",
                    lot=lot.name, hay=libre, ya=ya_recibido))
            created |= Reception.create({
                'backend_id': backend.id,
                'company_id': backend.company_id.id,
                'mapping_id': mapping.id,
                'product_id': lot.product_id.id,
                'lot_id': lot.id,
                'quantity': qty,
            })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Recepción para venta'),
            'res_model': 'amunet.woo.reception',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created.ids)],
            'target': 'current',
        }
