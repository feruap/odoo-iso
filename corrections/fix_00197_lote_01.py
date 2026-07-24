# AMP/IN/00197: repunta las 2 lineas a los lotes 01 existentes (vacios) y borra
# los lotes 02/03 autogenerados. SPHMC53->HMC53072601(1767), SPHMC54->HMC54072601(1768).
# Autorizado por Fernando 2026-07-20.
p = env['stock.picking'].search([('name', '=', 'AMP/IN/00197')], limit=1)
assert p and p.state == 'assigned', 'picking 00197 inesperado'
targets = {'SPHMC53': 1767, 'SPHMC54': 1768}  # lotes 01 existentes (0 cm)
Q = env['stock.quant'].sudo()
for line in p.move_line_ids:
    code = line.product_id.default_code
    if code not in targets:
        continue
    old_lot = line.lot_id
    tgt = env['stock.lot'].browse(targets[code])
    assert tgt.exists(), 'no existe lote destino de %s' % code
    print('%s: %s -> %s' % (code, line.lot_name, tgt.name))
    line.write({'lot_id': tgt.id, 'lot_name': tgt.name})
    # borrar el lote 02/03 viejo si quedo sin uso (0 existencia, sin lineas)
    if old_lot and old_lot.id != tgt.id:
        refs = env['stock.move.line'].search_count([('lot_id', '=', old_lot.id)])
        qty = sum(Q.search([('lot_id', '=', old_lot.id)]).mapped('quantity'))
        if refs == 0 and abs(qty) < 0.0001:
            nm = old_lot.name
            old_lot.unlink()
            print('   borrado lote vacio %s' % nm)
        else:
            print('   NO borrado %s (refs=%s qty=%s)' % (old_lot.name, refs, qty))
env.cr.commit()
print('LISTO 00197 -> 01')
