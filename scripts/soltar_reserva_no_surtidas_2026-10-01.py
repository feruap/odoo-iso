# 1026/01/VID y 1026/01/CRD estaban apartando material sin haberse surtido:
# cero renglones con cantidad surtida, y arrancan el 2 y el 5 de octubre.
# Odoo reserva solo al confirmar, y eso dejaba sin material a las ordenes que
# SI estan produciendo hoy (Mery, 1-oct-2026).
# Soltar la reserva no pierde nada: se vuelve a reservar cuando Almacen surta.
print('=== lo que tenian apartado sin haber surtido ===')
for nombre in ('1026/01/VID', '1026/01/CRD'):
    mo = env['mrp.production'].search([('name', '=', nombre)])
    for m in mo.move_raw_ids.sorted(lambda x: x.product_id.default_code or ''):
        for l in m.move_line_ids:
            print('   %-12s %-9s %-13s %9s' % (
                nombre, m.product_id.default_code, l.lot_id.name or '-', l.quantity))
    mo.do_unreserve()
    mo.message_post(body=(
        'Se solto la reserva automatica: esta orden tenia material apartado sin '
        'haberse surtido un solo renglon, y eso dejaba sin existencia a las '
        'ordenes que ya estan produciendo. El material se vuelve a reservar '
        'cuando Almacen la surta.'))
env.cr.commit()
print()
print('=== bolsas BOL01072501 libres ahora ===')
for q in env['stock.quant'].search([
        ('product_id.default_code', '=', 'MPBOL01'),
        ('location_id.usage', '=', 'internal'), ('quantity', '>', 0)]):
    print('   %-13s %-26s hay %9s  libre %9s' % (
        q.lot_id.name, q.location_id.complete_name, q.quantity,
        q.quantity - q.reserved_quantity))
