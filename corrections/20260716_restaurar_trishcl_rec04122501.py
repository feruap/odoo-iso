env = env(su=True)

tmpl = env['product.template'].search([('default_code', '=', 'MPREC04')])
producto = tmpl.product_variant_ids[0]
print("Producto:", tmpl.default_code, '-', tmpl.name)

lote = env['stock.lot'].create({
    'name': 'REC04122501',
    'product_id': producto.id,
    'company_id': 1,
    'expiration_date': '2026-06-19 00:00:00',
})
print("Lote recreado:", lote.name, '| Cad:', lote.expiration_date)

ubicacion = env['stock.location'].browse(5)
env['stock.quant']._update_available_quantity(
    product_id=producto,
    location_id=ubicacion,
    quantity=5000,
    lot_id=lote,
)

env.cr.commit()
print("Inventario: 5000 g de REC04122501 en", ubicacion.complete_name)
