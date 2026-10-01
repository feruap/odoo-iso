# Cancela las entradas que nacieron al autorizar de solicitudes que nadie
# compro. No toca AMP/IN/00487 (papeleria de Tony Tiendas, ya pagada).
for nombre, sol in (('AMP/IN/00470', 'SC/2026/00002'),
                    ('AMP/IN/00485', 'SC/2026/00006')):
    pk = env['stock.picking'].search([('name', '=', nombre)])
    if pk.state in ('done', 'cancel'):
        print(nombre, 'ya estaba', pk.state, '- no se toca')
        continue
    if any(pk.move_ids.mapped('picked')):
        print(nombre, 'TIENE LINEAS SURTIDAS - no se toca')
        continue
    pk.action_cancel()
    pk.message_post(body=(
        'Cancelada el 30-sep-2026. Esta entrada nacio al AUTORIZAR la '
        'solicitud %s, cuando el material todavia no se habia comprado: '
        'aparecia como pendiente para Almacen sin que nadie la hubiera '
        'pedido al proveedor. Desde hoy la entrada se genera al marcar la '
        'solicitud como Comprada, y cuando eso pase se creara una nueva con '
        'las cantidades de la compra real.'
    ) % sol)
    print(nombre, '->', pk.state)
env.cr.commit()
print()
print('=== como queda la lista de Almacen ===')
for p in env['stock.picking'].search([
        ('amunet_solicitud_compra_id', '!=', False)], order='name'):
    print(' ', p.name, p.state, '|', p.amunet_solicitud_compra_id.name,
          p.amunet_solicitud_compra_id.state)
