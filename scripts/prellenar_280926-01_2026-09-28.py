# Prerrellena la solucion 280926-01 (SPCDS01 Citrato de sodio 1%, 10 pz) y la
# deja lista para supervision. Pedido por Mery, 28-sep-2026. SOLO STAGING.
#
# "Terminada" exige tres cosas por componente (stock_move._compute_amunet_is_valid):
#   cantidad utilizada > 0, dentro del rango de pesaje del producto, y la
#   marca de disolucion -salvo el agua, que es el solvente y no la lleva-.
MO_ID = 191
mo = env['mrp.production'].browse(MO_ID)
assert mo.amunet_is_solution_product, 'no es una solucion'

for m in mo.move_raw_ids.filtered(lambda x: x.state != 'cancel'):
    pedido = m.product_uom_qty
    if not m.move_line_ids:
        q = env['stock.quant'].sudo().search([
            ('product_id', '=', m.product_id.id), ('location_id.usage', '=', 'internal'),
            ('quantity', '>', 0)], order='quantity desc', limit=1)
        env['stock.move.line'].sudo().create({
            'move_id': m.id, 'product_id': m.product_id.id,
            'product_uom_id': m.product_uom.id,
            'lot_id': q.lot_id.id if q.lot_id else False, 'quantity': pedido,
            'location_id': m.location_id.id, 'location_dest_id': m.location_dest_id.id,
            'company_id': m.company_id.id})
    else:
        m.move_line_ids[0].quantity = pedido
    vals = {'quantity': pedido}
    if 'amunet_qty_used' in m._fields:
        vals.update({'amunet_qty_used': pedido, 'amunet_qty_supplied': pedido})
    if not m._amunet_is_water_solvent():
        vals['amunet_dissolution'] = True
    m.sudo().write(vals)

env.cr.commit()          # se guarda ANTES de intentar la supervision
mo.invalidate_recordset()

print('=== prerrellenada ===')
for m in mo.move_raw_ids.filtered(lambda x: x.state != 'cancel'):
    print('  %-10s usado=%-9s lote=%-16s disolucion=%-6s valida=%s'
          % (m.product_id.default_code, m.quantity,
             m.move_line_ids[:1].lot_id.name or '-',
             getattr(m, 'amunet_dissolution', '-'), m.amunet_is_valid))
print('  SOLUCION TERMINADA: %s' % mo.amunet_solucion_terminada)
