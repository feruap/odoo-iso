# PRODUCCION: las ordenes de manufactura dejan de apartar material al
# confirmarse. (Mery, 1-oct-2026, despues de probarlo en staging)
#
# El problema: una orden confirmada para dentro de dos semanas competia por el
# material con la que se fabrica hoy. 1026/01/VID y 1026/01/CRD arrancan el 2 y
# el 5 de octubre, no tienen UN SOLO renglon surtido, y tenian apartadas 4,408
# bolsas y 3,600 viales de buffer. 0926/01/CCF, en produccion, no podia
# completar sus 150 bolsas por eso. Y soltarlo a mano no servia: entraron 340
# piezas por un ajuste y CRD se llevo 718 un segundo despues.
#
# Probado en staging con el usuario de Almacen antes de aplicar:
#  - at_confirm: reserva soltada -> entran 500 piezas -> vuelve a apartar sola.
#  - manual:     reserva soltada -> entran 500 piezas -> sigue en cero.
#  - Al INICIAR EL SURTIDO el material se aparta y los lotes se prellenan igual
#    que antes: para Almacen el flujo no cambia, solo el momento.
#
# NO se usa by_date: exigiria encender "Procurement: run scheduler", que esta
# apagado y ademas dispara las reglas de reabastecimiento.
#
# Para revertir: reservation_method = 'at_confirm' en los 5 tipos mrp_operation.
tipos = env['stock.picking.type'].search([('code', '=', 'mrp_operation')])
for t in tipos:
    print('   %-34s %s -> manual' % (t.warehouse_id.name or t.name, t.reservation_method))
tipos.write({'reservation_method': 'manual'})
env.cr.commit()
print()
print('=== como queda ===')
for t in env['stock.picking.type'].search([('code', '=', 'mrp_operation')]):
    print('   %-34s %s' % (t.warehouse_id.name or t.name, t.reservation_method))
print()
print('=== ordenes abiertas y lo que tienen apartado AHORA (no se toca) ===')
for mo in env['mrp.production'].search([('state', 'in', ('confirmed', 'progress', 'to_close'))]):
    ap = sum(mo.move_raw_ids.move_line_ids.mapped('quantity'))
    print('   %-14s %-10s apartado: %s' % (mo.name, mo.state, ap))
