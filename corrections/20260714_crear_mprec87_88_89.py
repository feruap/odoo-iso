env = env(su=True)

productos = [
    ('MPREC87', 'Arena de resina termoendurecible'),
    ('MPREC88', 'Agar Mueller Hinton Mcolab'),
    ('MPREC89', 'Calceína (fluorexona)'),
]

for codigo, nombre in productos:
    tmpl = env['product.template'].with_context(amunet_alta_autorizada=True).create({
        'name': nombre,
        'default_code': codigo,
        'categ_id': 18,
        'type': 'consu',
        'is_storable': True,
        'tracking': 'lot',
        'uom_id': 46,
        'purchase_ok': True,
        'sale_ok': True,
        'use_expiration_date': True,
    })
    print(f"  ✓ {tmpl.default_code} — {tmpl.name}")

env.cr.commit()
print("Listo. 3 productos creados.")
