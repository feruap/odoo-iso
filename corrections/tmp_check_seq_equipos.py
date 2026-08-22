equipos = env['product.template'].search([
    ('default_code', 'like', 'EQ%'),
    ('tracking', '=', 'lot'),
])
print(f"Equipos con tracking=lot: {len(equipos)}")
for p in equipos:
    prod = p.product_variant_ids[:1]
    seq = prod.lot_sequence_id
    print(f"  [{p.default_code}] {p.name} | seq={seq.code if seq else 'SIN SECUENCIA'}")
