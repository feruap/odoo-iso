# Las tres ordenes abiertas anteriores al cambio quedaron con el flujo de
# "material al piso" apagado (amunet_consumo_al_conciliar = False), asi que
# cuando Produccion firmo la recepcion del surtido el material NO salio del
# anaquel de Almacen. Las 22 ordenes nuevas si lo tienen. (Mery, 1-oct-2026)
#
# Se enciende en las tres. Se mueve al piso solo donde Produccion YA firmo:
#  - 0826/01/DCZ: firmo el 2-sep  -> se mueve ahora
#  - 0926/01/CCF: firmo el 28-sep -> NO se mueve todavia, su buffer tiene DOS
#    lotes y _amunet_lote_del_move solo toma el primero: moveria 3,750 piezas
#    de un lote que tiene 3,535. Queda pendiente de arreglar el metodo.
#  - 0826/01/ECO: aun no firma -> se movera solo cuando Produccion reciba.
for nombre in ('0826/01/DCZ', '0826/01/ECO', '0926/01/CCF'):
    mo = env['mrp.production'].search([('name', '=', nombre)])
    mo.sudo().amunet_consumo_al_conciliar = True
    print('%s: flujo encendido' % nombre)

mo = env['mrp.production'].search([('name', '=', '0826/01/DCZ')])
antes = {}
for m in mo.move_raw_ids:
    antes[m.product_id.default_code] = m.location_id.complete_name
picking = mo.sudo()._amunet_surtido_a_piso()
print()
print('traslado creado:', picking.name if picking else 'NINGUNO')
env.cr.commit()
print()
print('=== DCZ: de donde sale ahora cada componente ===')
for m in mo.move_raw_ids.sorted(lambda x: x.product_id.default_code or ''):
    print('   %-9s %-26s -> %s' % (
        m.product_id.default_code, antes.get(m.product_id.default_code, '?'),
        m.location_id.complete_name))
