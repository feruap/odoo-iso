# STBTR02: baja de los lotes que caducan ANTES de septiembre 2028 (Mery,
# 1-oct-2026). El criterio: el insumo tiene que durar lo que dura el producto
# terminado, dos anios, y estos ya no llegan.
#
# Se excluye el BTR01032601 (30.09.28) por decision expresa de Mery: cae en
# septiembre, no antes, y ademas tiene 215 piezas surtidas a 0926/01/CCF.
#
# El BTR122502 (30.06.28) ya se habia ajustado a cero antes, a mano.
#
# Estos dos quedaron libres hoy al soltarse la reserva de 1026/01/CRD, una
# orden que arranca el 5 de octubre y no tiene un solo renglon surtido.
CORTE = '2028-09-01'
MOTIVO = ('Baja por caducidad corta (1-oct-2026): caduca antes de septiembre '
          'de 2028 y el insumo tiene que durar los dos anios que dura el '
          'producto terminado.')
bajas = []
for q in env['stock.quant'].search([
        ('product_id', '=', 837), ('location_id.usage', '=', 'internal'),
        ('quantity', '>', 0)]):
    cad = q.lot_id.expiration_date
    if not cad or cad.strftime('%Y-%m-%d') >= CORTE:
        continue
    if q.reserved_quantity:
        print('OJO %s tiene %s reservadas: no se toca' % (q.lot_id.name, q.reserved_quantity))
        continue
    bajas.append((q.lot_id.name, cad.date(), q.quantity, q.location_id.complete_name))
    q.inventory_quantity = 0
    q.inventory_quantity_set = True
    q.action_apply_inventory()

prod = env['product.product'].browse(837)
if bajas:
    detalle = ''.join('<li><b>%s</b> (caduca %s): %s piezas</li>' % (n, c, int(qt))
                      for n, c, qt, _u in bajas)
    prod.product_tmpl_id.message_post(body=(
        'Baja de inventario por <b>caducidad corta</b>:<ul>%s</ul>%s<br/>'
        'Se dejan fuera a proposito: el BTR01032601 (30.09.28, cae en septiembre '
        'y tiene 215 piezas surtidas a 0926/01/CCF) y el BTR122502, que ya se '
        'habia ajustado antes.' % (detalle, MOTIVO)))
env.cr.commit()

print('=== dado de baja ===')
total = 0
for n, c, qt, u in bajas:
    print('   %-13s %-11s %9s   %s' % (n, c, qt, u))
    total += qt
print('   TOTAL:', total, 'viales')
print()
print('=== como queda el buffer ===')
for q in env['stock.quant'].search([
        ('product_id', '=', 837), ('location_id.usage', '=', 'internal'),
        ('quantity', '!=', 0)]).sorted(lambda x: x.lot_id.expiration_date or False):
    print('   %-13s %-11s hay %8s  libre %8s  %s' % (
        q.lot_id.name, q.lot_id.expiration_date.date(), q.quantity,
        q.quantity - q.reserved_quantity, q.location_id.complete_name))
