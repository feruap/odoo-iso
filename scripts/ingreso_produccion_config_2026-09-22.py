# -*- coding: utf-8 -*-
"""Configura el tipo de operacion 'Ingreso de produccion' como RECEPCION.

Con Validar debe bastar. El archivo de datos lleva noupdate="1", asi que estos
valores NO se aplican solos al actualizar el modulo: hay que correr esto.

  - use_create_lots = False : el lote viene de la orden de fabricacion. Si
    Almacen pudiera inventar uno, se rompe la trazabilidad.
  - create_backorder = never : o llego o no llego. Si Almacen recibe menos,
    corrige la cantidad y valida, sin dejar un pendiente fantasma.
  - show_operations = False : el lote y la cantidad ya vienen puestos.

Y da de alta el tipo en los accesos por almacen: amunet_warehouse_access filtra
por TIPO DE OPERACION, asi que un tipo nuevo da AccessError hasta que se agrega
a cada acceso restringido.

Decision de Mery, 22-sep-2026.

Correr con:
  /opt/odoo/scripts/run_correction.sh production ingreso_produccion_config_2026-09-22.py
"""

tipo = env.ref('amunet_production.picking_type_ingreso_produccion',
               raise_if_not_found=False)
loc = env.ref('amunet_production.stock_location_amp_entrada_interna',
              raise_if_not_found=False)
almacen = env['stock.warehouse'].search([('code', '=', 'AMP')], limit=1)

if not (tipo and loc and almacen):
    print('FALTA algo: tipo=%s ubicacion=%s almacen=%s' % (
        bool(tipo), bool(loc), bool(almacen)))
else:
    # la ubicacion cuelga de AMP, no de AMP/Entrada
    if loc.location_id != almacen.view_location_id:
        print('ubicacion: %s' % loc.complete_name)
        loc.sudo().write({'location_id': almacen.view_location_id.id})
        loc.invalidate_recordset()
    print('ubicacion: %s' % loc.complete_name)

    print('\ntipo de operacion antes: crear_lotes=%s backorder=%s' % (
        tipo.use_create_lots, tipo.create_backorder))
    tipo.sudo().write({
        'default_location_src_id': loc.id,
        'default_location_dest_id': almacen.lot_stock_id.id,
        'warehouse_id': almacen.id,
        'use_create_lots': False,
        'use_existing_lots': True,
        'create_backorder': 'never',
        'show_operations': False,
    })
    print('tipo de operacion ahora: crear_lotes=%s usar_existentes=%s backorder=%s' % (
        tipo.use_create_lots, tipo.use_existing_lots, tipo.create_backorder))
    print('   %s -> %s' % (tipo.default_location_src_id.complete_name,
                           tipo.default_location_dest_id.complete_name))

    print('\naccesos por almacen:')
    for acc in env['amunet.warehouse.access'].search(
            [('warehouse_id', '=', almacen.id)]):
        if acc.access_type != 'restricted':
            print('   %-40s acceso completo' % acc.display_name[:38])
            continue
        if tipo in acc.operation_type_ids:
            print('   %-40s ya lo tenia' % acc.display_name[:38])
            continue
        acc.sudo().write({'operation_type_ids': [(4, tipo.id)]})
        print('   %-40s -> agregado' % acc.display_name[:38])

env.cr.commit()
