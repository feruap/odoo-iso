# -*- coding: utf-8 -*-
"""Etapa 2: piso de produccion y marca de flujo por orden.

1. Crea la ubicacion "Piso de produccion" en cada almacen y la deja declarada
   en su configuracion. NO se reutilizan las ubicaciones "Preproduccion" que
   Odoo crea al configurar el almacen: existen pero estan ARCHIVADAS y
   pertenecen a la configuracion de pasos del almacen; tocarlas mezclaria dos
   cosas distintas.

   Se crea por ORM y no por SQL directo: stock.location tiene campos calculados
   y almacenados (complete_name, parent_path) que el INSERT crudo deja vacios.
   Con complete_name en blanco la ubicacion existe pero rompe la validacion de
   los traslados. Probado sobre clon: primero se hizo por SQL y fallo asi.

2. Las ordenes que YA existen terminan con el flujo viejo. Las que ya surtieron
   material bajo el comportamiento anterior quedarian a medio camino: material
   anotado como surtido pero sin movimiento, y un cierre que ya no lo iba a
   postear. Decision de Mery, 09-sep-2026.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

NOMBRE_PISO = 'Piso de producción'


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})

    # --- 1. Piso de produccion por almacen ---
    Location = env['stock.location']
    for wh in env['stock.warehouse'].search([]):
        if wh.amunet_loc_piso_id or not wh.view_location_id:
            continue
        piso = Location.search([
            ('location_id', '=', wh.view_location_id.id),
            ('usage', '=', 'internal'),
            ('name', '=', NOMBRE_PISO),
        ], limit=1)
        if not piso:
            piso = Location.create({
                'name': NOMBRE_PISO,
                'location_id': wh.view_location_id.id,
                'usage': 'internal',
                'company_id': wh.company_id.id,
            })
            _logger.info('Almacen %s (%s): creada ubicacion de piso %s (id %s)',
                         wh.name, wh.code, piso.complete_name, piso.id)
        wh.amunet_loc_piso_id = piso.id

    # --- 2. Las ordenes existentes se quedan con el flujo anterior ---
    cr.execute("""
        UPDATE mrp_production
           SET amunet_consumo_al_conciliar = FALSE
         WHERE amunet_consumo_al_conciliar IS DISTINCT FROM FALSE
    """)
    _logger.info('%s ordenes existentes se quedan con el flujo anterior '
                 '(inventario al cerrar).', cr.rowcount)
