# Borra las 11 recepciones AMP/IN/00201..00211 (creadas y validadas por error) y
# crea UNA sola orden de ingreso en BORRADOR con las 11 lineas, sin validar, para
# que Fernando la revise y valide. Atomico (commit al final).
# Autorizado por Fernando 2026-07-20.
Q = env['stock.quant'].sudo()
QC = env['amunet.quality.check']

# --- 1) Borrar las 11 recepciones ---
nombres = ['AMP/IN/%05d' % n for n in range(201, 212)]
borradas = []
for nm in nombres:
    p = env['stock.picking'].search([('name', '=', nm)], limit=1)
    if not p:
        continue
    lots = p.move_line_ids.mapped('lot_id')
    flots = p.move_line_ids.mapped('factory_lot_id')
    qcs = QC.search([('lot_id', 'in', lots.ids)])
    if qcs:
        if 'destination_line_ids' in qcs._fields:
            qcs.mapped('destination_line_ids').unlink()
        qcs.unlink()
    for m in p.move_ids:
        m.write({'state': 'draft'})
    p.move_line_ids.unlink()
    Q.search([('lot_id', 'in', lots.ids)]).unlink()
    p.move_ids.unlink()
    p.unlink()
    lots.unlink()
    flots.unlink()
    borradas.append(nm)
print('Borradas:', len(borradas), borradas)

# --- 2) Crear UNA orden en borrador con las 11 lineas ---
items = [
    ('SPHMC33', 60,  'T00326060002'),
    ('SPHMC27', 150, 'I00826060001'),
    ('SPHMC59', 60,  'C00826060001'),
    ('SPHMC28', 150, 'I06026060001'),
    ('SPHMC55', 30,  'O0082606000-1'),
    ('SPHMC48', 30,  'I01226060003'),
    ('SPHMC05', 60,  'I02526060002'),
    ('SPHMC06', 180, 'I09926060003'),
    ('SPHMC32', 30,  'I04826060001'),
    ('SPHMC42', 90,  'O01226060001'),
    ('SPHMC43', 60,  'I03526060002'),
]
pt = env['stock.picking.type'].browse(1)
src = pt.default_location_src_id or env.ref('stock.stock_location_suppliers')
dest = pt.default_location_dest_id
picking = env['stock.picking'].create({
    'picking_type_id': pt.id, 'partner_id': 321,
    'location_id': src.id, 'location_dest_id': dest.id,
    'origin': 'Ingreso HM lote julio2026 (11 hojas maestras)',
})
plan = []
for code, qty, lote in items:
    prod = env['product.product'].search([('default_code', '=', code)], limit=1)
    lot_name = 'HMC' + code[5:] + '072601'
    move = env['stock.move'].create({
        'description_picking': prod.display_name, 'picking_id': picking.id,
        'product_id': prod.id, 'product_uom_qty': float(qty), 'product_uom': prod.uom_id.id,
        'location_id': src.id, 'location_dest_id': dest.id,
    })
    plan.append((move, lot_name, float(qty), lote))
picking.action_confirm()
for move, lot_name, qty, lote in plan:
    ml = move.move_line_ids[:1]
    if not ml:
        ml = env['stock.move.line'].create({
            'move_id': move.id, 'picking_id': picking.id, 'product_id': move.product_id.id,
            'product_uom_id': move.product_uom.id, 'location_id': src.id, 'location_dest_id': dest.id})
    ml.write({'lot_name': lot_name, 'quantity': qty, 'expiration_date': '2028-05-01 09:00:00'})
    move.write({'amunet_supplier_lot': lote, 'amunet_exp_date': '01/05/2028', 'amunet_mfg_date': '01/06/2026'})
print('ORDEN NUEVA:', picking.name, '| estado:', picking.state, '| lineas:', len(picking.move_ids))
env.cr.commit()
print('COMMIT OK')
