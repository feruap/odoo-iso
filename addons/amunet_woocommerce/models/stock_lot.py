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

    El candado duro (no recibir lo no liberado) vive en ``amunet.woo.reception``.
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
        """El almacén de venta (woolibre) ACEPTA la recepción del lote.

        Crea una ``amunet.woo.reception`` por la existencia LIBRE del lote en la
        ubicación de piezas de APT. El candado de liberación vive en la
        recepción: si Calidad no liberó el lote, la creación falla con un aviso
        claro. Soporta parciales creando después más recepciones del mismo lote.
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
            backend = mapping.backend_id
            qty = backend._apt_released_qty_for_lot(lot)
            if qty <= 0:
                raise UserError(_(
                    "El lote %s no tiene existencia libre en el almacén de "
                    "piezas de APT para recibir.") % lot.name)
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
