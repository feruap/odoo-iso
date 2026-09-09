# -*- coding: utf-8 -*-
"""Marca el centro de trabajo donde Produccion resguarda el producto terminado.

A partir de esta version, terminar una actividad en ese centro INGRESA el
terminado al almacen. Antes el inventario solo se movia al cerrar la orden, y
por eso hacian falta altas manuales para vender o analizar producto que ya
existia fisicamente.

Se resuelve por CODIGO de centro de trabajo, no por id: los ids difieren entre
entornos y una migracion que los asuma marcaria el centro equivocado.
"""
import logging

_logger = logging.getLogger(__name__)

CODIGO_RESGUARDO = 'PTT'


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        SELECT id, name FROM mrp_workcenter WHERE code = %s
    """, (CODIGO_RESGUARDO,))
    filas = cr.fetchall()
    if not filas:
        _logger.warning(
            'No se encontro el centro de trabajo de resguardo (code=%s). '
            'El ingreso automatico del terminado quedara inactivo hasta que '
            'se marque a mano el campo amunet_es_resguardo_pt.',
            CODIGO_RESGUARDO)
        return
    cr.execute("""
        UPDATE mrp_workcenter SET amunet_es_resguardo_pt = TRUE WHERE code = %s
    """, (CODIGO_RESGUARDO,))
    for wc_id, nombre in filas:
        _logger.info(
            'Centro de trabajo %s (id %s) marcado como resguardo de PT.',
            nombre, wc_id)
