env = env(su=True)

tmpl = env['product.template'].search([('default_code', '=', 'MPREC37')])
producto = tmpl.product_variant_ids[0]
print("Producto:", tmpl.default_code, '-', tmpl.name)

factory = env['amunet.lot.factory'].search([('name', '=', '160719')], limit=1)
if not factory:
    factory = env['amunet.lot.factory'].create({'name': '160719'})
print("Lote fábrica:", factory.name)

lote = env['stock.lot'].create({
    'name': 'REC37032301',
    'product_id': producto.id,
    'company_id': 1,
    'factory_lot_id': factory.id,
    'expiration_date': '2026-12-01 00:00:00',
})
print("Lote creado:", lote.name, '| Proveedor:', factory.name, '| Cad:', lote.expiration_date)

ubicacion = env['stock.location'].browse(5)
env['stock.quant']._update_available_quantity(
    product_id=producto,
    location_id=ubicacion,
    quantity=500,
    lot_id=lote,
)

env.cr.commit()
print("Inventario: 500 ml de REC37032301 en", ubicacion.complete_name)
