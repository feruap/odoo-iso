p = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'EQBAD01')
], limit=1)
if not p:
    print("NO ENCONTRADO en esta base")
else:
    print(f"id={p.id}")
    print(f"name={p.name}")
    print(f"default_code={p.default_code}")
    print(f"type={p.type}")
    print(f"tracking={p.tracking}")
    print(f"categ_id={p.categ_id.complete_name} (id={p.categ_id.id})")
    print(f"uom_id={p.uom_id.name} (id={p.uom_id.id})")
    print(f"use_expiration_date={p.use_expiration_date}")
    print(f"amunet_requires_quarantine={p.amunet_requires_quarantine}")
    print(f"description={p.description or ''}")
    print(f"active={p.active}")
    prod = p.product_variant_ids[:1]
    seq = prod.lot_sequence_id
    print(f"lot_sequence={seq.code if seq else 'NINGUNA'}")
