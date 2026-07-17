env = env(su=True)

# Crear producto nuevo
categoria = env['product.category'].browse(18)  # Materia prima/Reactivo
uom_g = env['uom.uom'].browse(46)  # Gramos

tmpl = env['product.template'].with_context(amunet_alta_autorizada=True).create({
    'name': 'Agar bacteriológico',
    'default_code': 'MPREC90',
    'type': 'consu',
    'is_storable': True,
    'tracking': 'lot',
    'categ_id': categoria.id,
    'uom_id': uom_g.id,
})
print("Producto creado:", tmpl.default_code, '-', tmpl.name)

producto = tmpl.product_variant_ids[0]

# Crear lote
factory = env['amunet.lot.factory'].search([('name', '=', 'AB-2512140')], limit=1)
if not factory:
    factory = env['amunet.lot.factory'].create({'name': 'AB-2512140'})
print("Lote fábrica:", factory.name)

lote = env['stock.lot'].create({
    'name': 'REC90072601',
    'product_id': producto.id,
    'company_id': 1,
    'factory_lot_id': factory.id,
    'expiration_date': '2029-12-30 00:00:00',
})
print("Lote creado:", lote.name, '| Proveedor:', factory.name, '| Cad:', lote.expiration_date)

# Registrar inventario
ubicacion = env['stock.location'].browse(5)
env['stock.quant']._update_available_quantity(
    product_id=producto,
    location_id=ubicacion,
    quantity=450,
    lot_id=lote,
)

env.cr.commit()
print("Inventario: 450 g de REC90072601 en", ubicacion.complete_name)
