env = env(su=True)

ubicacion = env['stock.location'].browse(5)

lotes_data = [
    {
        'code': 'MPREC72',
        'lot_name': 'REC72052501',
        'factory_lot': '260329',
        'expiration': '2030-05-23 00:00:00',
        'qty': 295,
        'uom': 'g',
    },
    {
        'code': 'MPREC47',
        'lot_name': 'REC47042601',
        'factory_lot': '241224',
        'expiration': '2030-01-01 00:00:00',
        'qty': 900,
        'uom': 'g',
    },
    {
        'code': 'MPREC71',
        'lot_name': 'REC71052601',
        'factory_lot': '26AC1212',
        'expiration': '2031-05-18 00:00:00',
        'qty': 25,
        'uom': 'g',
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
    print(f"  {d['code']} | {lote.name} | Prov: {factory.name} | Cad: {lote.expiration_date} | {d['qty']} {d['uom']}")

env.cr.commit()
print("Listo. 3 lotes creados.")
