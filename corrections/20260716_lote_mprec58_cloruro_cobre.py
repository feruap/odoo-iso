env = env(su=True)

tmpl = env['product.template'].search([('default_code', '=', 'MPREC58')])
producto = tmpl.product_variant_ids[0]
print("Producto:", tmpl.default_code, '-', tmpl.name)

factory = env['amunet.lot.factory'].search([('name', '=', '250622')], limit=1)
if not factory:
    factory = env['amunet.lot.factory'].create({'name': '250622'})
print("Lote fábrica:", factory.name)

lote = env['stock.lot'].create({
    'name': 'REC58082201',
    'product_id': producto.id,
    'company_id': 1,
    'factory_lot_id': factory.id,
    'expiration_date': '2027-06-01 00:00:00',
})
print("Lote creado:", lote.name, '| Proveedor:', factory.name, '| Cad:', lote.expiration_date)

ubicacion = env['stock.location'].browse(5)
env['stock.quant']._update_available_quantity(
    product_id=producto,
    location_id=ubicacion,
    quantity=20,
    lot_id=lote,
)

env.cr.commit()
print("Inventario: 20 g de REC58082201 en", ubicacion.complete_name)
