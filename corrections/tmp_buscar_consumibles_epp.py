productos = env['product.template'].search([
    ('default_code', 'like', 'CO'),
    ('categ_id.name', 'ilike', 'consumible'),
    '|', '|',
    ('name', 'ilike', 'guante'),
    ('name', 'ilike', 'cofia'),
    ('name', 'ilike', 'nitrilo'),
], order='default_code')

if not productos:
    # Buscar sin filtro de categoría
    productos = env['product.template'].search([
        '|', '|',
        ('name', 'ilike', 'guante'),
        ('name', 'ilike', 'cofia'),
        ('name', 'ilike', 'nitrilo'),
    ], order='default_code')

for p in productos:
    prod = p.product_variant_ids[:1]
    seq = prod.lot_sequence_id
    print(f"[{p.default_code}] {p.name} | tracking={p.tracking} | seq={seq.code if seq else 'SIN SECUENCIA'} | req_q={p._amunet_effective_requires_quarantine()}")
