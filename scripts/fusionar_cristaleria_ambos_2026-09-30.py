# OPCION A (Mery, 30-sep-2026): una sola ficha por articulo, marcada "ambos".
# Matraz 2 L, probeta 250 ml y probeta 1 L se usan adentro Y se venden.
# Las fichas PT gemelas (PTCRS03/04, creadas el 23-sep) nacieron para el lado
# de venta, pero no llegaron a usarse: cero movimientos, cero ventas, cero
# existencia. Se BORRAN -- no se archivan -- para que nadie se las encuentre
# manana sin el contexto y vuelva a partir el articulo en dos.
adt = env['stock.warehouse'].search([('code', '=', 'ADT')], limit=1)

print('=== 1) borrar las fichas de venta sin usar ===')
for clave in ['PTCRS03', 'PTCRS04']:
    p = env['product.product'].with_context(active_test=False).search(
        [('default_code', '=', clave)], limit=1)
    if not p:
        print('  ', clave, 'ya no existe'); continue
    usado = (env['stock.move'].search_count([('product_id', '=', p.id)])
             or env['sale.order.line'].search_count([('product_id', '=', p.id)])
             or env['purchase.order.line'].search_count([('product_id', '=', p.id)]))
    if usado:
        print('  ', clave, 'TIENE MOVIMIENTO: no se borra'); continue
    t = p.product_tmpl_id
    env['product.value'].search([('product_id', '=', p.id)]).unlink()
    nombre = t.name
    t.unlink()
    print('   borrado %s (%s)' % (clave, nombre))

print()
print('=== 2) una sola ficha, en los dos almacenes y vendible ===')
for clave in ['COMEL02', 'COPRB04', 'COPRB05']:
    p = env['product.product'].with_context(active_test=False).search(
        [('default_code', '=', clave)], limit=1)
    t = p.product_tmpl_id
    antes = (p.active, t.amunet_destino_almacen, t.sale_ok)
    if not p.active:
        p.active = True          # COPRB05 tenia la variante archivada
    t.write({'amunet_destino_almacen': 'ambos', 'sale_ok': True,
             'marketplace_enabled': True})
    print('   %-8s %-24s antes=(activa=%s, destino=%s, vendible=%s) -> ahora=(activa=%s, destino=%s, vendible=%s)'
          % (clave, t.name[:24], antes[0], antes[1], antes[2],
             p.active, t.amunet_destino_almacen, t.sale_ok))

print()
print('=== 3) esta compra es para distribucion ===')
req = env['amunet.solicitud.compra'].search([('name', '=', 'SC/2026/00002')])
for l in req.line_ids:
    l.warehouse_id = adt.id
    print('   %-42s -> %s' % (l.name, l.warehouse_id.name))
req.message_post(body=(
    'Matraz y probetas pasan a vivir en los <b>dos</b> almacenes: se usan '
    'adentro y tambien se venden. Se borraron las fichas gemelas PTCRS03 y '
    'PTCRS04, que se habian creado para el lado de venta y nunca se usaron: '
    'un solo articulo, una sola clave. Las piezas de esta compra son para '
    'distribucion, asi que todo el pedido entra al <b>Almacen de '
    'Distribucion</b>. Un producto marcado "ambos" no se puede adivinar: el '
    'almacen se dice compra por compra, en cada renglon.'))
env.cr.commit()

print()
print('=== como queda ===')
for t in env['product.template'].search([('amunet_destino_almacen', '=', 'ambos')]):
    print('   ambos:', t.default_code, t.name[:38])
print('   probetas que quedan:',
      env['product.product'].with_context(active_test=False).search(
          [('default_code', 'like', 'PRB')]).mapped('default_code'),
      env['product.product'].search([('name', 'ilike', 'probeta')]).mapped('default_code'))
