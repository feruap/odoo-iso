env = env(su=True)

producto = env['product.template'].search([('default_code', '=', 'MPREC42')]).product_variant_ids[0]
lote = env['stock.lot'].search([('name', '=', 'REC42082401'), ('product_id', '=', producto.id)], limit=1)

print("Lote:", lote.name, "| Caducidad anterior:", lote.expiration_date)
lote.expiration_date = '2028-02-01 00:00:00'
print("Caducidad nueva:", lote.expiration_date)

env.cr.commit()
print("Listo.")
