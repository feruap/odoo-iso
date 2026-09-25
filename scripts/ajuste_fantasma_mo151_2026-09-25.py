# MO 151 (0926/01/HCG): 40 piezas fantasma en APT/Almacen Temporal PT.
#
# ORIGEN. El resguardo de producto terminado posteo al almacen la cantidad que la
# orden traia en ese momento (1,100 el 21-sep 16:12). Dos dias despues se corrigio
# que lo realmente fabricado eran 1,060, y se ajusto en la orden -- pero el
# movimiento de inventario ya estaba en 'done' y nadie lo toco.
#
# LA CUENTA. La orden produjo 1,060 piezas:
#     40 las destruyo Calidad en la prueba  -> Desechos
#  1,020 deberian estar en el anaquel       -> APT/Almacen Temporal PT
# Hoy hay 1,060 en el temporal + 40 en desechos = 1,100. Sobran 40.
#
# Bajar 40 del temporal deja coherentes la orden Y el almacen a la vez: la orden
# sigue diciendo que fabrico 1,060, y esas 1,060 quedan repartidas en 1,020 de
# anaquel mas 40 destruidas. No es un parche, es el numero correcto.
#
# NO aplica el criterio del 23-sep ("duplicado, el producto ya estaba contado por
# su entrega"): estas piezas no se entregaron ni se contaron dos veces. Nunca
# existieron.

LOTE, UBIC, QUITAR = '0926/01/HCG', 'APT/Almacén Temporal PT', 40.0

lot = env['stock.lot'].search([('name', '=', LOTE)], limit=1)
assert lot, 'no existe el lote %s' % LOTE
loc = env['stock.location'].search([('complete_name', '=', UBIC)], limit=1)
assert loc, 'no existe la ubicacion %s' % UBIC

q = env['stock.quant'].sudo().search([('lot_id', '=', lot.id), ('location_id', '=', loc.id)], limit=1)
assert q, 'el lote no tiene existencia en %s' % UBIC

def foto(titulo):
    print('--- %s' % titulo)
    for x in env['stock.quant'].sudo().search([('lot_id', '=', lot.id), ('quantity', '!=', 0)]):
        print('     %-42s %s' % (x.location_id.complete_name, x.quantity))

foto('ANTES')
antes = q.quantity
nuevo = antes - QUITAR
assert nuevo >= 0, 'quedaria en negativo'

q.inventory_quantity = nuevo
q.inventory_diff_quantity = nuevo - antes
q.inventory_quantity_set = True
q.with_context(inventory_mode=True)._apply_inventory()
env.cr.commit()

foto('DESPUES')

mo = env['mrp.production'].browse(151)
mo.message_post(body=(
    'Ajuste 25-sep-2026: se bajaron <b>40</b> pieza(s) de <b>%s</b> '
    '(de %s a %s). El resguardo del 21-sep posteo al almacen 1,100 pieza(s), '
    'que era lo que la orden traia entonces; el 23-sep se corrigio que lo '
    'fabricado fueron 1,060, pero el movimiento de inventario ya estaba cerrado '
    'y quedo sin ajustar. Con esto la cuenta cierra: 1,060 fabricadas = 1,020 en '
    'el anaquel + 40 que destruyo Calidad en la prueba.'
) % (UBIC, antes, nuevo))
env.cr.commit()
print('\nconstancia dejada en el historial de %s' % mo.name)
