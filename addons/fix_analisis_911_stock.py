Check = env['amunet.quality.check']
check = Check.browse(911)
print(f"Análisis id=911: number={check.analysis_number}, state={check.state}, qty_sampling={check.qty_sampling}")
print(f"Producto: {check.product_id.default_code}")
print(f"Lote: {check.lot_id.name} (id={check.lot_id.id})")

# Ver ubicaciones disponibles para agregar stock
Location = env['stock.location']
locs = Location.search([('usage', '=', 'internal'), ('active', '=', True)], limit=5)
print("\nUbicaciones internas disponibles:")
for l in locs:
    print(f"  id={l.id} — {l.complete_name}")

# Ver stock actual del lote
Quant = env['stock.quant']
quants = Quant.search([('lot_id', '=', check.lot_id.id)])
print(f"\nStock actual del lote {check.lot_id.name}: {len(quants)} registros")
for q in quants:
    print(f"  id={q.id}, ubicacion={q.location_id.complete_name}, qty={q.quantity}, reservado={q.reserved_quantity}")
