# Tres lotes con existencia en APT/Control de calidad que NO existe fisicamente.
# Son restos de muestreos que ya se consumieron o se repitieron y nunca se
# descontaron. Mery lo confirmo el 23-sep-2026: solo 0926/01/ZKC sigue vivo
# (su orden no se ha cerrado); estos tres son material inexistente.
#
# Se saca con ajuste de inventario y motivo escrito, no borrando movimientos:
# el historial de como llego ahi se conserva.
LOTES = {
    '0826/01/SAL': 'DLSAN01',
    '0926/02/PSS': 'DMPSA01',
    '0525/01/TGM': 'DMTOR02',
}
MOTIVO = ('Ajuste 23-sep-2026: resto de muestreo que ya no existe fisicamente. '
          'Confirmado por Mery (Desarrollo). No se descuenta 0926/01/ZKC porque '
          'su orden de fabricacion sigue abierta.')

L = env['stock.lot']; Q = env['stock.quant']
cuarentena = env['stock.location'].search(
    [('complete_name', 'like', 'APT/Control de calidad')], limit=1)
assert cuarentena, 'No se encontro APT/Control de calidad'

total = 0
for nombre, clave in LOTES.items():
    lot = L.search([('name', '=', nombre)], limit=1)
    if not lot:
        print('  no existe el lote %s' % nombre); continue
    quants = Q.search([('lot_id', '=', lot.id), ('location_id', 'child_of', cuarentena.id),
                       ('quantity', '!=', 0)])
    pz = sum(quants.mapped('quantity'))
    if not pz:
        print('  %-14s ya estaba en cero' % nombre); continue
    quants.with_context(inventory_mode=True).write({
        'inventory_quantity': 0.0, 'inventory_diff_quantity': -pz})
    quants.with_context(inventory_mode=True).action_apply_inventory()
    lot.message_post(body=MOTIVO)
    total += pz
    print('  descontadas %6s pz  %-14s %s' % (pz, nombre, clave))

env.cr.commit()
print('\ntotal descontado: %s pz' % total)
print('\n--- que queda en APT/Control de calidad ---')
for q in Q.search([('location_id', 'child_of', cuarentena.id), ('quantity', '!=', 0)]):
    print('   %-9s %-14s %s pz' % (q.product_id.default_code, q.lot_id.name or '-', q.quantity))
