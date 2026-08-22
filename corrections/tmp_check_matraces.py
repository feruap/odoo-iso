prods = env['product.template'].search([
    ('name', 'ilike', 'matraz')
], order='default_code')
for p in prods:
    prod = p.product_variant_ids[:1]
    seq = prod.lot_sequence_id
    print(f"[{p.default_code}] {p.name}")
    print(f"  tracking={p.tracking} | req_q={p._amunet_effective_requires_quarantine()}")
    print(f"  categ={p.categ_id.complete_name}")
    print(f"  seq={seq.code if seq else 'SIN SECUENCIA'} | prefix={seq.prefix if seq else '-'}")
