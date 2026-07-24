# Corrige 3 lotes atorados por el bug de destino en la liberacion QC:
#  - CAR27072601 (557) y BPR03072601 (487): su liberacion quedo 'done' pero movio
#    Control de calidad -> Control de calidad; se hace traslado interno trazable
#    Control de calidad -> Existencias.
#  - CAC08072601 (1680): su liberacion AMP/IN/00219 sigue 'assigned' con destino mal
#    (Entrada); se corrige el destino a Existencias y se DEJA para que Almacen valide.
# Autorizado por Fernando 2026-07-22. Fix de raiz ya en Main (8892bef).
CC = env['stock.location'].browse(7)   # AMP/Entrada/Control de calidad
EXIST = env['stock.location'].browse(5)  # AMP/Existencias
ptype = env['stock.picking.type'].sudo().search([
    ('code', '=', 'internal'), ('warehouse_id.code', '=', 'AMP')], limit=1)

def mover_a_existencias(lot_name):
    lot = env['stock.lot'].sudo().search([('name', '=', lot_name)], limit=1)
    assert lot, 'no existe %s' % lot_name
    env.cr.execute("""SELECT sum(quantity) FROM stock_quant WHERE lot_id=%s AND location_id=%s""", (lot.id, CC.id))
    qty = env.cr.fetchone()[0] or 0.0
    if qty <= 0:
        print('  %s: sin stock en Control de calidad, omitido' % lot_name); return
    pick = env['stock.picking'].sudo().create({
        'picking_type_id': ptype.id, 'location_id': CC.id, 'location_dest_id': EXIST.id,
        'origin': 'Correccion destino liberacion QC %s' % lot_name,
        'move_ids': [(0, 0, {
            'product_id': lot.product_id.id, 'product_uom_qty': qty,
            'product_uom': lot.product_id.uom_id.id,
            'location_id': CC.id, 'location_dest_id': EXIST.id})],
    })
    pick.action_confirm(); pick.action_assign()
    if pick.move_line_ids:
        for ml in pick.move_line_ids:
            ml.lot_id = lot.id; ml.quantity = qty
    else:
        env['stock.move.line'].create({
            'picking_id': pick.id, 'move_id': pick.move_ids[0].id,
            'product_id': lot.product_id.id, 'product_uom_id': lot.product_id.uom_id.id,
            'location_id': CC.id, 'location_dest_id': EXIST.id, 'lot_id': lot.id, 'quantity': qty})
    pick.with_context(skip_backorder=True).button_validate()
    print('  %s -> %s (%s u) estado %s' % (lot_name, pick.name, qty, pick.state))

for ln in ['CAR27072601', 'BPR03072601']:
    mover_a_existencias(ln)

# CAC08: corregir destino de la liberacion pendiente y dejar para Almacen
pick = env['stock.picking'].sudo().search([('name', '=', 'AMP/IN/00219')], limit=1)
assert pick and pick.state not in ('done', 'cancel'), 'AMP/IN/00219 no editable'
pick.move_ids.write({'location_dest_id': EXIST.id})
pick.move_line_ids.write({'location_dest_id': EXIST.id})
pick.write({'location_dest_id': EXIST.id})
print('  AMP/IN/00219 (CAC08) destino corregido a Existencias, estado %s (pendiente de Almacen)' % pick.state)

env.cr.commit()
print('=== ubicaciones finales ===')
env.cr.execute("""
  SELECT l.name, sl.complete_name, sq.quantity FROM stock_quant sq
  JOIN stock_location sl ON sl.id=sq.location_id JOIN stock_lot l ON l.id=sq.lot_id
  WHERE l.name IN ('CAR27072601','BPR03072601','CAC08072601') AND sq.quantity<>0 AND sl.usage='internal'
  ORDER BY l.name, sl.complete_name""")
for row in env.cr.fetchall():
    print('   ', row)
print('LISTO')
