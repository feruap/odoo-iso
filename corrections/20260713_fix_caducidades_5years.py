env = env(su=True)

ajustes = [
    ('REC10052501', 'MPREC10', '2030-05-09 00:00:00'),
    ('REC06012301', 'MPREC06', '2028-01-16 00:00:00'),
    ('REC06052301', 'MPREC06', '2028-05-02 00:00:00'),
    ('REC06022401', 'MPREC06', '2029-02-12 00:00:00'),
    ('REC61062601', 'MPREC61', '2031-06-18 00:00:00'),
]

for lot_name, code, nueva_cad in ajustes:
    producto = env['product.template'].search([('default_code', '=', code)]).product_variant_ids[0]
    lote = env['stock.lot'].search([('name', '=', lot_name), ('product_id', '=', producto.id)], limit=1)
    cad_anterior = lote.expiration_date
    lote.expiration_date = nueva_cad
    print(f"  {lot_name} | {cad_anterior} -> {lote.expiration_date}")

env.cr.commit()
print("Listo. 5 lotes actualizados a +5 años.")
