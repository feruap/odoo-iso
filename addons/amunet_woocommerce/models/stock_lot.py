# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class StockLot(models.Model):
    """Publica a la tienda un lote cuando Calidad lo LIBERA.

    Este es el disparador regulatorio correcto: solo el producto liberado puede
    reflejarse como existencia vendible. Idempotente (ledger) y seguro (no
    bloquea la liberacion si la tienda no responde). Solo actua si el modulo de
    calidad aporta el campo ``amunet_lot_release_state``.
    """

    _inherit = "stock.lot"

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
