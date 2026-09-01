# -*- coding: utf-8 -*-

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class StockLot(models.Model):
    """Publica a la tienda un lote cuando Calidad lo LIBERA.

    Este es el disparador regulatorio correcto: solo el producto liberado puede
    reflejarse como existencia vendible. Idempotente (ledger) y seguro (no
    bloquea la liberacion si la tienda no responde). Solo actua si el modulo de
    calidad aporta el campo ``amunet_lot_release_state``.
    """

    _inherit = "stock.lot"

    # Marca del material que entro como INVENTARIO INICIAL (migracion de
    # papel a digital). No es un lote fabricado bajo el sistema: es
    # material anterior a el. Se marca para poder distinguirlo despues en
    # cualquier revision o auditoria, en vez de que se confunda con un
    # lote nacido del proceso.
    amunet_origen_inicial = fields.Boolean(
        string='Inventario inicial', default=False, copy=False, index=True,
        help='Marcado: estas piezas se cargaron como inventario inicial al '
             'pasar del control en papel al sistema. No tienen orden de '
             'fabricacion ni liberacion de Calidad porque son anteriores '
             'al sistema; su constancia es el ajuste de inventario.')

    def write(self, vals):
        res = super().write(vals)
        if vals.get("amunet_lot_release_state") == "released":
            try:
                Backend = self.env["amunet.woo.backend"]
                for lot in self:
                    if "amunet_lot_release_state" not in lot._fields:
                        break
                    if lot.amunet_lot_release_state == "released" and lot.product_id:
                        Backend._auto_publish_product_lots(
                            lot.product_id, lot=lot)
            except Exception:  # noqa: BLE001 - jamas debe bloquear la liberacion
                _logger.exception(
                    "Auto-publicacion Woo tras liberacion de lote fallo (ignorado)")
        return res
