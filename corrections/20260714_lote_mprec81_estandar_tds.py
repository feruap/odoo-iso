env = env(su=True)

tmpl = env['product.template'].search([('default_code', '=', 'MPREC81')])
print("Producto:", tmpl.default_code, '-', tmpl.name, '| UOM actual:', tmpl.uom_id.name)

uom_ml = env['uom.uom'].browse(11)
tmpl.uom_id = uom_ml
print("UOM cambiada a:", tmpl.uom_id.name)

producto = tmpl.product_variant_ids[0]

factory = env['amunet.lot.factory'].search([('name', '=', 'S250703065')], limit=1)
if not factory:
    factory = env['amunet.lot.factory'].create({'name': 'S250703065'})
print("Lote fábrica:", factory.name)

lote = env['stock.lot'].create({
    'name': 'REC81100101',
    'product_id': producto.id,
    'company_id': 1,
    'factory_lot_id': factory.id,
    'expiration_date': '2026-10-01 00:00:00',
})
print("Lote creado:", lote.name, '| Proveedor:', factory.name, '| Cad:', lote.expiration_date)

ubicacion = env['stock.location'].browse(5)
env['stock.quant']._update_available_quantity(
    product_id=producto,
    location_id=ubicacion,
    quantity=400,
    lot_id=lote,
)

env.cr.commit()
print("Inventario: 400 ml de REC81100101 en", ubicacion.complete_name)
