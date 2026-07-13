env = env(su=True)

producto = env['product.template'].search([('default_code', '=', 'MPREC06')]).product_variant_ids[0]
lote = env['stock.lot'].search([('name', '=', 'REC06012301'), ('product_id', '=', producto.id)], limit=1)
ubicacion = env['stock.location'].browse(5)

print("Lote:", lote.name, "| Producto:", producto.name)

env['stock.quant']._update_available_quantity(
    product_id=producto,
    location_id=ubicacion,
    quantity=1000,
    lot_id=lote,
)

quant = env['stock.quant'].search([('product_id', '=', producto.id), ('lot_id', '=', lote.id), ('location_id', '=', ubicacion.id)], limit=1)
print("Nueva cantidad:", quant.quantity, "ml")

env.cr.commit()
print("Listo.")
