"""
setup_missing_components.py
Crea los componentes crudos (materia prima) faltantes necesarios para los BoMs
en staging si no existen, como 'Ácido Clorhídrico 37% HCl'.
"""

MISSING_PRODUCTS = [
    {'name': 'Ácido cloroáurico', 'uom': 'g', 'type': 'consu'},
    {'name': 'Agua tridestilada filtrada', 'uom': 'ml', 'type': 'consu'},
    {'name': 'Ácido Clorhídrico 37% HCl', 'uom': 'ml', 'type': 'consu'},
    {'name': 'Borato de sodio', 'uom': 'g', 'type': 'consu'},
    {'name': 'Cloruro de Potasio', 'uom': 'g', 'type': 'consu'},
    {'name': 'Fosfato de Sodio Dibásico', 'uom': 'g', 'type': 'consu'},
    {'name': 'Fosfato de Potasio Monobásico', 'uom': 'g', 'type': 'consu'},
    {'name': 'Tween 20X', 'uom': 'ml', 'type': 'consu'},
    {'name': 'Fosfato de Sodio Monobásico', 'uom': 'g', 'type': 'consu'},
    {'name': 'Caseína CHEMS', 'uom': 'g', 'type': 'consu'}
]

Product = env['product.template']
Uom = env['uom.uom']

created = 0
for data in MISSING_PRODUCTS:
    p = Product.search([('name', '=', data['name'])], limit=1)
    if p:
        print(f"[SKIP] componente ya existe: {data['name']}")
        continue

    uom = Uom.search([('name', '=', data['uom'])], limit=1)
    if not uom:
        uom = Uom.search([('name', 'ilike', data['uom'])], limit=1)
    if not uom:
        uom = env.ref('uom.product_uom_unit')

    Product.create({
        'name': data['name'],
        'type': data['type'],
        'uom_id': uom.id,
    })
    env.cr.commit()
    print(f"[OK] Componente creado: {data['name']} ({uom.name})")
    created += 1

print(f"\nResumen: {created} componentes creados.")
