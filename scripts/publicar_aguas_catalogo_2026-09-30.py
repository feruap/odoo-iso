# Publica las 3 aguas en el catalogo del marketplace interno.
# Sin liga de compra: no son compra en linea, se piden directo al proveedor
# (lo confirmo Mery el 30-sep-2026).
NOTA = ('Compra directa con el proveedor: no se pide por internet. '
        'Compras hace el pedido al proveedor habitual.')
claves = ['MPADE01', 'MPABI01', 'MPATR01']
for clave in claves:
    p = env['product.product'].search([('default_code', '=', clave)], limit=1)
    if not p:
        print(clave, 'NO EXISTE'); continue
    t = p.product_tmpl_id
    antes = (t.marketplace_enabled, t.marketplace_flow, t.amunet_destino_almacen)
    t.write({
        'marketplace_enabled': True,
        'marketplace_flow': 'general',
        'marketplace_request_note': NOTA,
    })
    print('%-8s %-28s antes=%s  ahora=(%s, %s, %s)' % (
        clave, t.name[:28], antes,
        t.marketplace_enabled, t.marketplace_flow, t.amunet_destino_almacen))
env.cr.commit()

print()
print('=== quedan visibles en el catalogo? (el domain del renglon) ===')
dom = [('product_tmpl_id.marketplace_enabled', '=', True),
       ('default_code', 'in', claves)]
print(' ', env['product.product'].search(dom).mapped('default_code'))
print()
print('publicados en total:',
      env['product.template'].search_count([('marketplace_enabled', '=', True)]))
