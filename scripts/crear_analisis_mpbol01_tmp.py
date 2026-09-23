PT    = env['product.template']
PP    = env['product.product']
Lot   = env['stock.lot']
Check = env['amunet.quality.check']

pt  = PT.search([('default_code', '=', 'MPBOL01')], limit=1)
pp  = PP.search([('product_tmpl_id', '=', pt.id)], limit=1)
lot = Lot.browse(2468)  # BOL01092601

print(f"Producto: {pt.default_code} — {pt.name}")
print(f"Lote:     {lot.name}")

check = Check.create({
    'product_id': pp.id,
    'lot_id':     lot.id,
    'analysis_type': 'initial',
    'qty_sampling':  5,
})

env.cr.commit()

print(f"\nAnálisis: {check.analysis_number} (id={check.id}), estado={check.state}")
print(f"Parámetros: {len(check.test_line_ids)}")
for tl in check.test_line_ids.sorted('sequence'):
    print(f"  [{tl.sequence}] {tl.code} — {tl.name}")
print("\n✓ Guardado en staging.")
