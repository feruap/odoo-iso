Check  = env['amunet.quality.check']
Quant  = env['stock.quant']
check  = Check.browse(911)

product  = check.product_id
lot      = check.lot_id
loc_amp  = env['stock.location'].browse(5)   # AMP/Existencias

print(f"Producto: {product.default_code}, Lote: {lot.name}")
print(f"Ubicacion: {loc_amp.complete_name} (usage={loc_amp.usage})")

# Agregar 10 unidades en AMP/Existencias
Quant.sudo()._update_available_quantity(product, loc_amp, 10.0, lot_id=lot)
env.cr.commit()

# Verificar resultado
check._compute_lot_qty_available()
print(f"\nlot_qty_available ahora: {check.lot_qty_available}")

quants_post = Quant.search([('lot_id', '=', lot.id), ('product_id', '=', product.id)])
for q in quants_post:
    print(f"  quant id={q.id}, loc={q.location_id.complete_name}, qty={q.quantity}")
