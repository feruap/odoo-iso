env = env(su=True)

tmpl = env['product.template'].search([('default_code', '=', 'MPREC09')])
producto = tmpl.product_variant_ids[0]
print("Producto:", tmpl.default_code, '-', tmpl.name)

factory = env['amunet.lot.factory'].search([('name', '=', '260624')], limit=1)
if not factory:
    factory = env['amunet.lot.factory'].create({'name': '260624'})
print("Lote fábrica:", factory.name)

lote = env['stock.lot'].create({
    'name': 'REC09122501',
    'product_id': producto.id,
    'company_id': 1,
    'factory_lot_id': factory.id,
    'expiration_date': '2029-06-01 00:00:00',
})
print("Lote creado:", lote.name, '| Proveedor:', factory.name, '| Cad:', lote.expiration_date)

ubicacion = env['stock.location'].browse(5)
env['stock.quant']._update_available_quantity(
    product_id=producto,
    location_id=ubicacion,
    quantity=1000,
    lot_id=lote,
)

env.cr.commit()
print("Inventario: 1000 g de REC09122501 en", ubicacion.complete_name)
