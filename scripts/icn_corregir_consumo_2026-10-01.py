# 0926/01/ICN (NT-proBNP): el consumo capturado era 359 -- las piezas
# producidas -- en TODOS los renglones por igual, incluidos la caja y el vial
# de corrimiento, que van uno por caja y no uno por pieza. Al cerrar habria
# descontado 359 cajas y 359 viales en vez de 39: 320 de cada uno de mas.
#
# Se deja proporcional a la receta (Mery, 1-oct-2026):
#   - lo que esta en el BoM: su cantidad por pieza x 359 producidas
#   - caja y vial (empaque, no estan en el BoM): lo que Almacen surtio, 39,
#     coherente con el plan de empaque aprobado (33 cajas de 10 + 8 de 5)
#
# El candado de stock.move solo deja a Almacen tocar el surtido y a produccion
# la cantidad; por eso el bypass documentado.
mo = env['mrp.production'].search([('name', '=', '0926/01/ICN')])
prod = mo.qty_producing
bom = {l.product_id.default_code: l.product_qty / (mo.bom_id.product_qty or 1)
       for l in mo.bom_id.bom_line_ids}

cambios = []
for m in mo.move_raw_ids:
    clave = m.product_id.default_code
    nuevo = round(bom[clave] * prod, 4) if clave in bom else m.amunet_qty_supplied
    if abs((m.amunet_qty_used or 0) - nuevo) < 0.0001:
        continue
    cambios.append((clave, m.amunet_qty_used, nuevo))
    m.sudo().with_context(amunet_supply_internal=True).write({
        'amunet_qty_used': nuevo,
        'quantity': nuevo,
    })

mo.message_post(body=(
    'Se corrigio el consumo de componentes: estaba capturado 359 -- las piezas '
    'producidas -- en todos los renglones por igual, incluidos la <b>Caja caple</b> '
    'y el <b>Vial de solucion de corrimiento</b>, que van uno por CAJA y no uno '
    'por pieza. Al cerrar la orden se habrian descontado 359 de cada uno en vez '
    'de 39: <b>320 cajas y 320 viales que nadie uso</b>. Queda proporcional a la '
    'receta, y el empaque segun el plan aprobado (33 cajas de 10 + 8 de 5).'))
env.cr.commit()

print('%-9s %12s -> %12s' % ('clave', 'antes', 'ahora'))
for c in cambios:
    print('%-9s %12s -> %12s' % c)
print()
print('=== como queda ===')
for m in mo.move_raw_ids.sorted(lambda x: x.product_id.default_code or ''):
    print('   %-9s requerido %8s | surtido %8s | usado %8s | descontara %8s' % (
        m.product_id.default_code, m.product_uom_qty, m.amunet_qty_supplied,
        m.amunet_qty_used, m.quantity))
