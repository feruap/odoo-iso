env = env(su=True)

tmpl = env['product.template'].search([('default_code', '=', 'MPREC38')])
print("Producto:", tmpl.default_code, '-', tmpl.name, '| UOM actual:', tmpl.uom_id.name)

uom_ml = env['uom.uom'].browse(11)
tmpl.uom_id = uom_ml
print("UOM cambiada a:", tmpl.uom_id.name)

producto = tmpl.product_variant_ids[0]

factory = env['amunet.lot.factory'].search([('name', '=', '27.0222')], limit=1)
if not factory:
    factory = env['amunet.lot.factory'].create({'name': '27.0222'})
print("Lote fábrica:", factory.name)

lote = env['stock.lot'].create({
    'name': 'REC38072201',
    'product_id': producto.id,
    'company_id': 1,
    'factory_lot_id': factory.id,
    'expiration_date': '2027-02-01 00:00:00',
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
print("Inventario: 20 ml de REC38072201 en", ubicacion.complete_name)
