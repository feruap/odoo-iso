PT    = env['product.template']
PP    = env['product.product']
Lot   = env['stock.lot']
Check = env['amunet.quality.check']

pt = PT.search([('default_code', '=', 'MICAJ01')], limit=1)
pp = PP.search([('product_tmpl_id', '=', pt.id)], limit=1)

# Buscar o crear un lote de prueba
lot = Lot.search([('product_id', '=', pp.id)], limit=1)
if not lot:
    lot = Lot.create({'name': 'CAJ01-TEST-001', 'product_id': pp.id})

print(f"Producto: {pt.default_code} — {pt.name}")
print(f"Lote: {lot.name}")

check = Check.create({
    'product_id': pp.id,
    'lot_id': lot.id,
    'analysis_type': 'initial',
    'qty_sampling': 5,
})

# Avanzar directo a in_progress + sampling_confirmed
check.sudo().write({'state': 'in_progress', 'sampling_confirmed': True})
env.cr.commit()

print(f"\nAnálisis: {check.analysis_number or f'id={check.id}'}")
print(f"Estado: {check.state}, sampling_confirmed: {check.sampling_confirmed}")
print("\nParámetros:")
for tl in check.test_line_ids.sorted('sequence'):
    print(f"  [{tl.sequence}] {tl.code} — {tl.name}")
    for d in tl.test_line_detail_ids.sorted('sequence'):
        print(f"       {d.name}: {d.evaluation_type}, rango={d.min_value}-{d.max_value}")
