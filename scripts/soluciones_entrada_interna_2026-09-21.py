# -*- coding: utf-8 -*-
"""Ajustes de datos del ingreso de Produccion a Almacen.

Acompana al codigo que hace que las soluciones entren a Almacen como
cualquier ingreso (Produccion es el proveedor) en vez de aparecer de golpe
en existencias.

Hace tres cosas:

1. Cuelga 'Entrada Interna' de AMP. El XML la crea bajo AMP/Entrada porque
   la ubicacion vista del almacen no tiene XMLID en esta base; aqui se
   reubica como hermana, para que lo que entrega Produccion no se mezcle con
   lo que Calidad libera de proveedores.

2. Da de alta el tipo de operacion 'Ingreso de produccion' en los accesos por
   almacen. Sin esto, Almacen recibe un AccessError al validar: el control de
   accesos trabaja por tipo de operacion y el tipo es nuevo.

3. SPSPC03 (Borato 0.1 M) vuelve a pedir analisis de calidad. Decision de
   Mery, 21-sep-2026: la entrega a Almacen espera la liberacion, asi que la
   solucion debe llevar analisis. Tiene 2 parametros configurados.

Correr con:
  /opt/odoo/scripts/run_correction.sh production soluciones_entrada_interna_2026-09-21.py
"""

almacen = env['stock.warehouse'].search([('code', '=', 'AMP')], limit=1)
loc = env.ref('amunet_production.stock_location_amp_entrada_interna',
              raise_if_not_found=False)
tipo = env.ref('amunet_production.picking_type_ingreso_produccion',
               raise_if_not_found=False)

if not (almacen and loc and tipo):
    print('FALTA algo: almacen=%s loc=%s tipo=%s' % (
        bool(almacen), bool(loc), bool(tipo)))
else:
    # 1. la ubicacion cuelga de AMP, no de AMP/Entrada
    print('ubicacion antes : %s' % loc.complete_name)
    if loc.location_id != almacen.view_location_id:
        loc.sudo().write({'location_id': almacen.view_location_id.id})
        loc.invalidate_recordset()
    print('ubicacion ahora : %s' % loc.complete_name)

    tipo.sudo().write({
        'default_location_src_id': loc.id,
        'default_location_dest_id': almacen.lot_stock_id.id,
        'warehouse_id': almacen.id,
    })
    print('tipo de operacion: %s | %s -> %s' % (
        tipo.name, tipo.default_location_src_id.complete_name,
        tipo.default_location_dest_id.complete_name))

    # 2. accesos por almacen
    print('\naccesos de AMP:')
    for acc in env['amunet.warehouse.access'].search(
            [('warehouse_id', '=', almacen.id)]):
        quien = acc.display_name
        if acc.access_type != 'restricted':
            print('  %-40s %s (acceso completo, no hace falta)' % (
                quien[:38], acc.access_type))
            continue
        if tipo in acc.operation_type_ids:
            print('  %-40s ya lo tenia' % quien[:38])
            continue
        acc.sudo().write({'operation_type_ids': [(4, tipo.id)]})
        print('  %-40s -> agregado "Ingreso de produccion"' % quien[:38])

# 3. SPSPC03 vuelve a pedir analisis
t = env['product.template'].search([('default_code', '=', 'SPSPC03')], limit=1)
if t:
    antes = t.amunet_req_quality_control
    t.amunet_req_quality_control = True
    n = env['amunet.quality.parameter.specification.config'].search_count(
        [('product_tmpl_id', '=', t.id)])
    print('\nSPSPC03 %s: pedia analisis=%s -> ahora=True (parametros: %s)' % (
        t.name, antes, n))

sols = env['product.template'].search(
    [('categ_id.complete_name', 'ilike', 'soluc')])
print('\nsoluciones que piden analisis: %d de %d' % (
    len(sols.filtered('amunet_req_quality_control')), len(sols)))

env.cr.commit()
