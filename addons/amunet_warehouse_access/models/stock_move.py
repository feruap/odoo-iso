# -*- coding: utf-8 -*-

from odoo import models

import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    """Que la linea de operacion siga al movimiento.

    En Odoo el destino de un traslado vive en DOS lugares: el del movimiento, que
    es el que se ve en la pantalla, y el de la linea de operacion, que es el que de
    verdad mueve el inventario. Al cambiar el de arriba, el de abajo se quedaba con
    el valor viejo y nadie lo notaba: arriba se veia bien y abajo estaba mal.

    Asi quedaron en falso cinco traslados Burgos -> Fabrica en agosto de 2026. El
    sistema los daba por hechos, el material nunca salio de Burgos, y los numeros no
    cuadraban en ninguno de los dos almacenes.
    """
    _inherit = 'stock.move'

    def write(self, vals):
        res = super().write(vals)
        if 'location_id' not in vals and 'location_dest_id' not in vals:
            return res
        for mv in self:
            if mv.state in ('done', 'cancel'):
                continue
            # Solo las lineas que todavia no se ejecutaron: lo hecho es historial.
            lineas = mv.move_line_ids.filtered(
                lambda ml: ml.state not in ('done', 'cancel'))
            if not lineas:
                continue
            cambios = {}
            if 'location_id' in vals and any(
                    ml.location_id != mv.location_id for ml in lineas):
                cambios['location_id'] = mv.location_id.id
            if 'location_dest_id' in vals and any(
                    ml.location_dest_id != mv.location_dest_id for ml in lineas):
                cambios['location_dest_id'] = mv.location_dest_id.id
            if cambios:
                lineas.write(cambios)
                _logger.info(
                    'amunet: lineas de %s alineadas al movimiento (%s)',
                    mv.reference or mv.id, ', '.join(cambios))
        return res
