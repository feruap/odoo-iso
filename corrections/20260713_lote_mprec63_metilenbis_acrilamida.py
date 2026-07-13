env = env(su=True)

tmpl = env['product.template'].search([('default_code', '=', 'MPREC63')])
producto = tmpl.product_variant_ids[0]
print("Producto:", tmpl.default_code, '-', tmpl.name)

factory = env['amunet.lot.factory'].search([('name', '=', '146072')], limit=1)
if not factory:
    factory = env['amunet.lot.factory'].create({'name': '146072'})
print("Lote fábrica:", factory.name)

lote = env['stock.lot'].create({
    'name': 'REC63032601',
    'product_id': producto.id,
    'company_id': 1,
    'factory_lot_id': factory.id,
    'expiration_date': '2031-03-26 00:00:00',
})
print("Lote creado:", lote.name, '| Proveedor:', factory.name, '| Cad:', lote.expiration_date)

ubicacion = env['stock.location'].browse(5)
env['stock.quant']._update_available_quantity(
    product_id=producto,
    location_id=ubicacion,
    quantity=90,
    lot_id=lote,
)

env.cr.commit()
print("Inventario: 90 g de REC63032601 en", ubicacion.complete_name)
