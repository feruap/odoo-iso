"""
Busca la orden SMP/26/00143 en varios modelos posibles.
"""
nombre = 'SMP/26/00143'

# stock.picking
picks = env['stock.picking'].search([('name', 'ilike', '00143')], limit=10)
print(f"stock.picking con '00143': {len(picks)}")
for p in picks:
    print(f"  {p.name} | {p.picking_type_id.name} | {p.state}")

print()

# Buscar también por origen
picks2 = env['stock.picking'].search([('origin', 'ilike', '00143')], limit=10)
print(f"stock.picking con origen '00143': {len(picks2)}")
for p in picks2:
    print(f"  {p.name} | origen={p.origin} | {p.state}")

print()

# mrp.production (órdenes de fabricación)
try:
    prods = env['mrp.production'].search([('name', 'ilike', '00143')], limit=10)
    print(f"mrp.production con '00143': {len(prods)}")
    for p in prods:
        print(f"  {p.name} | {p.state}")
except Exception as e:
    print(f"mrp.production: {e}")

print()

# stock.move con referencia
moves = env['stock.move'].search([('reference', 'ilike', 'SMP')], limit=5)
print(f"stock.move con ref 'SMP' (muestra): {len(moves)}")
for m in moves[:3]:
    print(f"  ref={m.reference} | {m.product_id.default_code} | {m.state}")
