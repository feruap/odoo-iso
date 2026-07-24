# El lote HMC27072601 (SPHMC27) se libero pero por el bug de destino en la
# liberacion QC (destination_line_ids) quedo en AMP/Entrada (148.20) en vez de
# AMP/Existencias. Se crea un traslado interno trazable AMP/Entrada -> AMP/Existencias
# y se valida. Autorizado por Fernando 2026-07-22. (El fix de raiz ya va en Main:
# commit 8892bef.)
Picking = env['stock.picking'].sudo()
Move = env['stock.move'].sudo()

lot = env['stock.lot'].sudo().search([('name', '=', 'HMC27072601')], limit=1)
assert lot, 'no existe HMC27072601'
src = env['stock.location'].browse(6)   # AMP/Entrada
dst = env['stock.location'].browse(5)   # AMP/Existencias
qty = 148.20

ptype = env['stock.picking.type'].sudo().search([
    ('code', '=', 'internal'), ('warehouse_id.code', '=', 'AMP')], limit=1)
assert ptype, 'sin tipo de operacion interna AMP'

pick = Picking.create({
    'picking_type_id': ptype.id,
    'location_id': src.id,
    'location_dest_id': dst.id,
    'origin': 'Correccion destino liberacion QC HMC27072601',
    'move_ids': [(0, 0, {
        'product_id': lot.product_id.id,
        'product_uom_qty': qty,
        'product_uom': lot.product_id.uom_id.id,
        'location_id': src.id,
        'location_dest_id': dst.id,
    })],
})
pick.action_confirm()
pick.action_assign()
for ml in pick.move_line_ids:
    ml.lot_id = lot.id
    ml.quantity = qty
if not pick.move_line_ids:
    env['stock.move.line'].create({
        'picking_id': pick.id, 'move_id': pick.move_ids[0].id,
        'product_id': lot.product_id.id, 'product_uom_id': lot.product_id.uom_id.id,
        'location_id': src.id, 'location_dest_id': dst.id,
        'lot_id': lot.id, 'quantity': qty,
    })
pick.with_context(skip_backorder=True).button_validate()
env.cr.commit()
print('Traslado:', pick.name, '| estado:', pick.state)

env.cr.execute("""
  SELECT sl.complete_name, sq.quantity FROM stock_quant sq
  JOIN stock_location sl ON sl.id=sq.location_id
  WHERE sq.lot_id=%s AND sq.quantity<>0 AND sl.usage='internal' ORDER BY sl.complete_name
""", (lot.id,))
print('HMC27072601 ahora:')
for row in env.cr.fetchall():
    print('   ', row)
print('LISTO')
