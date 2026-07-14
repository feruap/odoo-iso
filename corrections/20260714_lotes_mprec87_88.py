env = env(su=True)

ubicacion = env['stock.location'].browse(5)

lotes_data = [
    {
        'code': 'MPREC87',
        'lot_name': 'REC87122501',
        'factory_lot': '4002991100',
        'expiration': '2030-12-11 00:00:00',
        'qty': 2134,
    },
    {
        'code': 'MPREC88',
        'lot_name': 'REC88072601',
        'factory_lot': '713125D002',
        'expiration': '2029-04-01 00:00:00',
        'qty': 38,
    },
]

for d in lotes_data:
    tmpl = env['product.template'].search([('default_code', '=', d['code'])])
    producto = tmpl.product_variant_ids[0]

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
    print(f"  {d['code']} | {lote.name} | Prov: {factory.name} | Cad: {lote.expiration_date} | {d['qty']} g")

env.cr.commit()
print("Listo. 2 lotes creados.")
