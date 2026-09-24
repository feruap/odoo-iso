Check = env['amunet.quality.check']
check = Check.browse(911)

# Verificar usage de las ubicaciones
Quant = env['stock.quant']
quants = Quant.search([('lot_id', '=', 2468)])
for q in quants:
    print(f"  quant id={q.id}, loc={q.location_id.complete_name}, usage={q.location_id.usage}, qty={q.quantity}")

# Buscar ubicación interna AMP
Location = env['stock.location']
amp_locs = Location.search([('complete_name', 'ilike', 'AMP'), ('usage', '=', 'internal')])
print("\nUbicaciones internas AMP:")
for l in amp_locs:
    print(f"  id={l.id} — {l.complete_name} (usage={l.usage})")

# Usar original_qty_received como workaround directo
check.write({'original_qty_received': 215.0})
env.cr.commit()
check._compute_lot_qty_available()
print(f"\noriginal_qty_received={check.original_qty_received}, lot_qty_available={check.lot_qty_available}")
