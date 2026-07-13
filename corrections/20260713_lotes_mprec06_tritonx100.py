env = env(su=True)

tmpl = env['product.template'].search([('default_code', '=', 'MPREC06')])
producto = tmpl.product_variant_ids[0]
print("Producto:", tmpl.default_code, '-', tmpl.name)

ubicacion = env['stock.location'].browse(5)

lotes_data = [
    {
        'lot_name': 'REC06012301',
        'factory_lot': '791620491147001',
        'expiration': '2026-01-16 00:00:00',
        'qty': 1100,
    },
    {
        'lot_name': 'REC06052301',
        'factory_lot': '791620491147001',
        'expiration': '2026-05-02 00:00:00',
        'qty': 2000,
    },
    {
        'lot_name': 'REC06022401',
        'factory_lot': '791620492031001',
        'expiration': '2027-02-12 00:00:00',
        'qty': 2000,
    },
]

for d in lotes_data:
    factory = env['amunet.lot.factory'].search([('name', '=', d['factory_lot'])], limit=1)
    if not factory:
        factory = env['amunet.lot.factory'].create({'name': d['factory_lot']})

    lote = env['stock.lot'].create({
        'name': d['lot_name'],
        'product_id': producto.id,
        'company_id': 1,
        'factory_lot_id': factory.id,
        'expiration_date': d['expiration'],
    })

    env['stock.quant']._update_available_quantity(
        product_id=producto,
        location_id=ubicacion,
        quantity=d['qty'],
        lot_id=lote,
    )
    print(f"  Lote: {lote.name} | Proveedor: {factory.name} | Cad: {lote.expiration_date} | {d['qty']} ml")

env.cr.commit()
print("Listo. 3 lotes creados para MPREC06 Tritón X-100.")
