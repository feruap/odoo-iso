sin_seq = []
con_seq = []

prods = env['product.product'].with_context(active_test=False).search([
    ('tracking', '!=', 'none'),
])
for p in prods:
    seq = p.lot_sequence_id
    if not seq or not seq.code.startswith('amunet.lot.'):
        sin_seq.append(f"  {p.product_tmpl_id.default_code or '(sin código)':<14} {p.product_tmpl_id.name[:50]}")
    else:
        con_seq.append(p.product_tmpl_id.default_code)

print(f"Con secuencia Amunet: {len(con_seq)}")
print(f"Sin secuencia Amunet (lote genérico): {len(sin_seq)}")
print("\nSin secuencia:")
for l in sorted(sin_seq):
    print(l)
