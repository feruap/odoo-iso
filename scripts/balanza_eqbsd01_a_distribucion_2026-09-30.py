# La balanza semianalitica es producto de compra-venta (lo confirmo Mery el
# 30-sep-2026): al comprarla entra al Almacen de Distribucion, no al de
# Materia Prima. Se corrige en los dos lugares: la ficha y el renglon de la
# solicitud que todavia no se compra.
adt = env['stock.warehouse'].search([('code', '=', 'ADT')], limit=1)
prod = env['product.product'].search([('default_code', '=', 'EQBSD01')], limit=1)
tmpl = prod.product_tmpl_id
print('ficha antes :', tmpl.amunet_destino_almacen)
tmpl.write({'amunet_destino_almacen': 'adt'})
print('ficha ahora :', tmpl.amunet_destino_almacen)

req = env['amunet.solicitud.compra'].search([('name', '=', 'SC/2026/00002')])
lineas = req.line_ids.filtered(lambda l: l.product_id == prod)
for l in lineas:
    print('renglon antes:', l.name, '->', l.warehouse_id.name)
    l.warehouse_id = adt.id
    print('renglon ahora:', l.name, '->', l.warehouse_id.name)
req.message_post(body=(
    'La balanza semianalitica (EQBSD01) se redirige al <b>Almacen de '
    'Distribucion</b>: es producto de compra-venta, no de uso interno, asi '
    'que no entra por Materia Prima. El resto del pedido -- matraz y '
    'probetas -- si es de uso interno y sigue llegando a Materia Prima. '
    'Cuando se marque como comprada se generara una orden de recepcion por '
    'cada almacen.'))
env.cr.commit()

print()
print('=== como queda el pedido ===')
for l in req.line_ids:
    print('  %-42s %s -> %s' % (l.name, l.qty, l.warehouse_id.name))
