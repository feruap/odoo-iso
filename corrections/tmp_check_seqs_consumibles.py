consumibles = env['product.template'].search([
    ('categ_id.complete_name', 'ilike', 'consumible'),
    ('tracking', '!=', 'none'),
], order='default_code')

con_seq = []
sin_seq = []
for p in consumibles:
    prod = p.product_variant_ids[:1]
    seq = prod.lot_sequence_id
    if seq and seq.code.startswith('amunet.lot.'):
        con_seq.append((p.default_code, p.name, seq.prefix or ''))
    else:
        sin_seq.append((p.default_code, p.name, seq.code if seq else 'SIN SECUENCIA'))

print(f"Con secuencia Amunet: {len(con_seq)}")
print(f"Sin secuencia Amunet: {len(sin_seq)}")
if sin_seq:
    print("\nSin secuencia propia:")
    for code, name, seq in sin_seq:
        print(f"  [{code}] {name} | {seq}")
