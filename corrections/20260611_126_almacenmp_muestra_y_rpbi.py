# Crear categorías Consumible/RPBI y Consumible/Muestra con sus productos
# Solicitud de Karla (almacen.mp) — almacenables, unidades

cat_cons = env['product.category'].search([('complete_name', '=', 'Consumible')], limit=1)

# Categoría RPBI (por si no quedó del paso anterior)
cat_rpbi = env['product.category'].search([('complete_name', '=', 'Consumible / RPBI')], limit=1)
if not cat_rpbi:
    cat_rpbi = env['product.category'].create({'name': 'RPBI', 'parent_id': cat_cons.id})
    print("Categoría creada: Consumible / RPBI (id=" + str(cat_rpbi.id) + ")")

# Categoría Muestra
cat_muestra = env['product.category'].search([('complete_name', '=', 'Consumible / Muestra')], limit=1)
if not cat_muestra:
    cat_muestra = env['product.category'].create({'name': 'Muestra', 'parent_id': cat_cons.id})
    print("Categoría creada: Consumible / Muestra (id=" + str(cat_muestra.id) + ")")
else:
    print("Categoría ya existe: Consumible / Muestra (id=" + str(cat_muestra.id) + ")")

uom_units = env['uom.uom'].search([('name', '=', 'Units')], limit=1)

productos = [
    ('Bolsa RPBI Chica',                'COBRP01', cat_rpbi),
    ('Bolsa RPBI Mediana',              'COBRP02', cat_rpbi),
    ('Bolsa RPBI Grande',               'COBRP03', cat_rpbi),
    ('Tubo para toma de muestra rojo',  'COTMR01', cat_muestra),
    ('Tubo para toma de muestra lila',  'COTML01', cat_muestra),
    ('Aguja Vacutainer',                'COAVC01', cat_muestra),
    ('Vaso recolector de muestra',      'COVRM01', cat_muestra),
]

for nombre, clave, cat in productos:
    existe = env['product.template'].search([('default_code', '=', clave)], limit=1)
    if not existe:
        env['product.template'].create({
            'name': nombre,
            'default_code': clave,
            'categ_id': cat.id,
            'uom_id': uom_units.id,
            'type': 'consu',
            'is_storable': True,
            'purchase_ok': True,
            'sale_ok': False,
        })
        print("Creado: " + nombre + " (" + clave + ")")
    else:
        print("Ya existe: " + nombre + " (" + clave + ")")

env.cr.commit()
print("LISTO: COMMIT OK")
