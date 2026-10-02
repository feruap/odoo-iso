# Soltar la reserva de las dos ordenes que no se han surtido. Ya se hizo una
# vez hoy y se la volvieron a quedar en minutos, porque con at_confirm el
# sistema las reasignaba solas. Ahora, con reserva manual, se queda suelta.
# Arrancan el 2 y el 5 de octubre y no tienen un solo renglon surtido.
for nombre in ('1026/01/VID', '1026/01/CRD'):
    mo = env['mrp.production'].search([('name', '=', nombre)])
    antes = sum(mo.move_raw_ids.move_line_ids.mapped('quantity'))
    mo.do_unreserve()
    mo.invalidate_recordset()
    despues = sum(mo.move_raw_ids.move_line_ids.mapped('quantity'))
    print('%-14s apartado %9s -> %s' % (nombre, antes, despues))
    mo.message_post(body=(
        'Se solto el material apartado. Esta orden no tiene ningun renglon '
        'surtido y arranca despues, asi que ese material queda disponible para '
        'las ordenes que se estan fabricando ahora. Se vuelve a apartar cuando '
        'Almacen inicie su surtido.'))
env.cr.commit()
print()
print('=== material que queda libre ===')
for clave in ('MPBOL01', 'STBTR02', 'STDSC01'):
    pr = env['product.product'].search([('default_code', '=', clave)], limit=1)
    libre = sum(q.quantity - q.reserved_quantity for q in env['stock.quant'].search([
        ('product_id', '=', pr.id), ('location_id.usage', '=', 'internal')]))
    print('   %-9s %s' % (clave, libre))
