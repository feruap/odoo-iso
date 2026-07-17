env = env(su=True)

categoria = env['product.category'].browse(18)
uom_g = env['uom.uom'].browse(46)

tmpl = env['product.template'].with_context(amunet_alta_autorizada=True).create({
    'name': 'Base Agar Sangre',
    'default_code': 'MPREC91',
    'type': 'consu',
    'is_storable': True,
    'tracking': 'lot',
    'categ_id': categoria.id,
    'uom_id': uom_g.id,
})
print("Producto creado:", tmpl.default_code, '-', tmpl.name)

producto = tmpl.product_variant_ids[0]

factory = env['amunet.lot.factory'].search([('name', '=', '724123H005')], limit=1)
if not factory:
    factory = env['amunet.lot.factory'].create({'name': '724123H005'})
print("Lote fábrica:", factory.name)

lote = env['stock.lot'].create({
    'name': 'REC91072601',
    'product_id': producto.id,
    'company_id': 1,
    'factory_lot_id': factory.id,
    'expiration_date': '2028-08-01 00:00:00',
})
print("Lote creado:", lote.name, '| Proveedor:', factory.name, '| Cad:', lote.expiration_date)

ubicacion = env['stock.location'].browse(5)
env['stock.quant']._update_available_quantity(
    product_id=producto,
    location_id=ubicacion,
    quantity=100,
    lot_id=lote,
)

env.cr.commit()
print("Inventario: 100 g de REC91072601 en", ubicacion.complete_name)
