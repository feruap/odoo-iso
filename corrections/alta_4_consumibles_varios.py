# Alta de 4 consumibles nuevos en categoria Consumible / Varios.
# Solicitado por almacen (Karla) via staging; STESP01 se excluye (ya existe,
# se regresa a Karla para revision). Autorizado por Fernando 2026-07-21.
Categ = env['product.category'].sudo()
Tmpl = env['product.template'].sudo()

# 1) Categoria Consumible / Varios (parent Consumible)
padre = Categ.search([('name', '=', 'Consumible'), ('parent_id', '=', False)], limit=1)
assert padre, 'no existe la categoria padre Consumible'
varios = Categ.search([('name', '=', 'Varios'), ('parent_id', '=', padre.id)], limit=1)
if not varios:
    varios = Categ.create({'name': 'Varios', 'parent_id': padre.id})
    print('Categoria creada: Consumible / Varios id', varios.id)
else:
    print('Categoria Consumible / Varios ya existia id', varios.id)

# 2) Los 4 productos
productos = [
    ('COPIS01', 'Piseta'),
    ('COCAT01', 'Caja de almacenamiento de tubos PCR'),
    ('COTPH01', 'Tira para pH'),
    ('COCEN01', 'Centricon 0.5'),
]
for code, name in productos:
    if Tmpl.search([('default_code', '=', code)], limit=1):
        print('  YA existe, se omite:', code)
        continue
    t = Tmpl.with_context(amunet_alta_autorizada=True).create({
        'name': name,
        'default_code': code,
        'type': 'consu',
        'is_storable': True,
        'tracking': 'lot',
        'categ_id': varios.id,
        'uom_id': env.ref('uom.product_uom_unit').id,
        'purchase_ok': True,
        'sale_ok': True,
        'use_expiration_date': False,
    })
    print('  Creado:', code, name, '-> id', t.id)

env.cr.commit()
print('LISTO')
