# La orden 0926/01/VPL quedo con 8 de sus 9 componentes sin reservar y sin lote,
# aunque el material esta en AMP/Piso de produccion con su lote. Es el defecto
# de 'picked' pegado en True que ya se corrigio en codigo (commit d4d523d): el
# arreglo evita que vuelva a pasar, pero no cura la orden que ya quedo asi.
#
# Aqui se hace lo mismo que hara el flujo de ahora en adelante: bajar 'picked'
# y volver a reservar. La reserva toma los lotes que estan fisicamente en el
# piso, que son los que surtio Almacen.
#
# No se toca ninguna cantidad ni consumo: solo se restablece la reserva.
mo = env['mrp.production'].browse(152)
assert mo.exists() and mo.name == '0926/01/VPL', 'La orden 152 no es la esperada'

sin_reserva = mo.move_raw_ids.filtered(
    lambda m: m.state == 'confirmed' and m.picked and not m.quantity)
print('orden %s  estado=%s' % (mo.name, mo.state))
print('lineas a reparar: %s' % len(sin_reserva))
if not sin_reserva:
    print('nada que reparar')
else:
    for m in sin_reserva:
        m.sudo().picked = False
        m.sudo()._action_assign()
    mo.invalidate_recordset()
    env.cr.commit()

print('\n--- como queda la orden ---')
for m in mo.move_raw_ids.sorted('id'):
    lotes = ', '.join(ml.lot_id.name for ml in m.move_line_ids if ml.lot_id) or '-- SIN LOTE --'
    print('  %-9s %-28s estado=%-10s reservado=%-8s %s' % (
        m.product_id.default_code, (m.product_id.name or '')[:28],
        m.state, m.quantity, lotes))
