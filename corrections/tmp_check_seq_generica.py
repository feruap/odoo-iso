from collections import defaultdict

todos = env['product.template'].search([
    ('tracking', '!=', 'none'),
    ('type', '!=', 'service'),
], order='default_code')

sin_amunet = []
for p in todos:
    prod = p.product_variant_ids[:1]
    seq = prod.lot_sequence_id
    if not seq or not seq.code.startswith('amunet.lot.'):
        sin_amunet.append((p.default_code or '???', p.name, seq.code if seq else 'SIN SECUENCIA', p.categ_id.complete_name))

print(f"Total con tracking: {len(todos)}")
print(f"Sin secuencia Amunet: {len(sin_amunet)}\n")

por_categ = defaultdict(list)
for code, name, seq, categ in sin_amunet:
    por_categ[categ].append((code, name, seq))

for categ in sorted(por_categ.keys(), key=lambda x: str(x)):
    print(f"=== {categ} ===")
    for code, name, seq in sorted(por_categ[categ], key=lambda x: str(x[0])):
        print(f"  [{code}] {name} | {seq}")
