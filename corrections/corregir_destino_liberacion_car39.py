# Corrige el destino de la recepcion de liberacion AMP/IN/00218 (lote CAR39072601):
# quedo con destino Control de calidad (mismo origen) en vez de AMP/Existencias.
# Se corrige el destino en header + move + move_line, dejando el picking en
# estado 'assigned' para que Almacen lo valide manualmente.
# Autorizado por Fernando 2026-07-21. CAR59 NO se toca.
Picking = env['stock.picking'].sudo()
pick = Picking.search([('name', '=', 'AMP/IN/00218')], limit=1)
assert pick, 'no existe AMP/IN/00218'

wh = env['stock.warehouse'].sudo().search([('code', '=', 'AMP')], limit=1)
dest = wh.lot_stock_id  # AMP/Existencias
assert dest, 'no encontre la ubicacion de existencias de AMP'

print('Picking:', pick.name, '| estado:', pick.state)
print('Destino ANTES (header):', pick.location_dest_id.complete_name)
print('Destino NUEVO:', dest.complete_name)

# Seguridad: solo debe haber lineas del lote CAR39072601
lotes = pick.move_line_ids.mapped('lot_id.name')
print('Lotes en el picking:', lotes)
assert set(lotes) <= {'CAR39072601'}, 'ATENCION: el picking tiene otros lotes, abortar'

pick.write({'location_dest_id': dest.id})
for m in pick.move_ids:
    print('  move', m.id, ':', m.location_dest_id.complete_name, '->', dest.complete_name)
    m.write({'location_dest_id': dest.id})
for ml in pick.move_line_ids:
    ml.write({'location_dest_id': dest.id})

env.cr.commit()
print('LISTO. Estado final:', pick.state, '| destino:', pick.location_dest_id.complete_name)
