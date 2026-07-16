env = env(su=True)

tmpl = env['product.template'].search([('default_code', '=', 'MPREC68')])
producto = tmpl.product_variant_ids[0]
print("Producto:", tmpl.default_code, '-', tmpl.name)

factory = env['amunet.lot.factory'].search([('name', '=', 'N9905010')], limit=1)
if not factory:
    factory = env['amunet.lot.factory'].create({'name': 'N9905010'})
print("Lote fábrica:", factory.name)

lote = env['stock.lot'].create({
    'name': 'REC68022101',
    'product_id': producto.id,
    'company_id': 1,
    'factory_lot_id': factory.id,
    'expiration_date': '2028-02-05 00:00:00',
})
print("Lote creado:", lote.name, '| Proveedor:', factory.name, '| Cad:', lote.expiration_date)

ubicacion = env['stock.location'].browse(5)
env['stock.quant']._update_available_quantity(
    product_id=producto,
    location_id=ubicacion,
    quantity=300,
    lot_id=lote,
)

env.cr.commit()
print("Inventario: 300 g de REC68022101 en", ubicacion.complete_name)
