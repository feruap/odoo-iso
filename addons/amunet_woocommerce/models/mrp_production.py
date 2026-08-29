# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    """Al marcar una orden de fabricacion como hecha, intenta publicar a la
    tienda los lotes LIBERADOS del producto terminado (idempotente y seguro).

    Nota regulatoria: un lote recien fabricado suele estar 'pendiente' de
    liberacion por Calidad, por lo que normalmente aqui no se publica nada; la
    publicacion efectiva ocurre al LIBERAR el lote (ver stock_lot.py). Este
    enganche cubre el caso de lotes ya liberados y no bloquea el cierre de la MO.
    """

    _inherit = "mrp.production"

    def button_mark_done(self):
        res = super().button_mark_done()
        try:
            Backend = self.env["amunet.woo.backend"]
            for production in self:
                if production.state == "done" and production.product_id:
                    Backend._auto_publish_product_lots(production.product_id)
        except Exception:  # noqa: BLE001 - jamas debe bloquear la produccion
            _logger.exception(
                "Auto-publicacion Woo tras cierre de MO fallo (ignorado)")
        return res
