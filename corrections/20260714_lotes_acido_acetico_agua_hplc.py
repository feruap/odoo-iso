env = env(su=True)

ubicacion = env['stock.location'].browse(5)
uom_ml = env['uom.uom'].browse(11)

# --- Ácido acético (MPREC78) — cambiar UOM a ml ---
tmpl78 = env['product.template'].search([('default_code', '=', 'MPREC78')])
print("Producto:", tmpl78.default_code, '-', tmpl78.name, '| UOM actual:', tmpl78.uom_id.name)
tmpl78.uom_id = uom_ml
print("  UOM cambiada a ml")
prod78 = tmpl78.product_variant_ids[0]

factory_acido = env['amunet.lot.factory'].search([('name', '=', '140225')], limit=1)
if not factory_acido:
    factory_acido = env['amunet.lot.factory'].create({'name': '140225'})

lote78 = env['stock.lot'].create({
    'name': 'REC78062601',
    'product_id': prod78.id,
    'company_id': 1,
    'factory_lot_id': factory_acido.id,
    'expiration_date': '2030-03-01 00:00:00',
})
env['stock.quant']._update_available_quantity(product_id=prod78, location_id=ubicacion, quantity=1000, lot_id=lote78)
print(f"  Lote: {lote78.name} | Prov: {factory_acido.name} | Cad: {lote78.expiration_date} | 1000 ml")

# --- Agua HPLC (MPREC84) — cambiar UOM a ml ---
tmpl84 = env['product.template'].search([('default_code', '=', 'MPREC84')])
print("Producto:", tmpl84.default_code, '-', tmpl84.name, '| UOM actual:', tmpl84.uom_id.name)
tmpl84.uom_id = uom_ml
print("  UOM cambiada a ml")
prod84 = tmpl84.product_variant_ids[0]

factory_hplc = env['amunet.lot.factory'].search([('name', '=', '181023')], limit=1)
if not factory_hplc:
    factory_hplc = env['amunet.lot.factory'].create({'name': '181023'})

# Recepción 1: 05/03/2025 — 20 ml
lote84a = env['stock.lot'].create({
    'name': 'REC84032501',
    'product_id': prod84.id,
    'company_id': 1,
    'factory_lot_id': factory_hplc.id,
    'expiration_date': '2028-10-01 00:00:00',
})
env['stock.quant']._update_available_quantity(product_id=prod84, location_id=ubicacion, quantity=20, lot_id=lote84a)
print(f"  Lote: {lote84a.name} | Prov: {factory_hplc.name} | Cad: {lote84a.expiration_date} | 20 ml")

# Recepción 2: 14/07/2026 — 4000 ml
lote84b = env['stock.lot'].create({
    'name': 'REC84072601',
    'product_id': prod84.id,
    'company_id': 1,
    'factory_lot_id': factory_hplc.id,
    'expiration_date': '2028-10-01 00:00:00',
})
env['stock.quant']._update_available_quantity(product_id=prod84, location_id=ubicacion, quantity=4000, lot_id=lote84b)
print(f"  Lote: {lote84b.name} | Prov: {factory_hplc.name} | Cad: {lote84b.expiration_date} | 4000 ml")

env.cr.commit()
print("Listo. 3 lotes creados.")
