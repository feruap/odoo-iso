# Crear categoría Consumible/Celofán y sus tres productos con secuencia de lote

cat_padre = env['product.category'].search([('name', '=', 'Consumible')], limit=1)

cat_cel = env['product.category'].search([
    ('name', '=', 'Celofán'), ('parent_id', '=', cat_padre.id)
], limit=1)
if not cat_cel:
    cat_cel = env['product.category'].create({
        'name': 'Celofán',
        'parent_id': cat_padre.id,
    })
    print("Categoría CREADA: %s" % cat_cel.complete_name)
else:
    print("Categoría ya existía: %s" % cat_cel.complete_name)

productos_def = [
    ('COBCE01', 'Bolsa de celofán 6x15+3',  'BCE01'),
    ('COBCE02', 'Bolsa de celofán 10x15+3', 'BCE02'),
    ('COBCE03', 'Bolsa de celofán 10x20+3', 'BCE03'),
]

for codigo, nombre, prefijo in productos_def:
    existente = env['product.template'].search([('default_code', '=', codigo)], limit=1)
    if existente:
        print("[%s] Ya existía — actualizando" % codigo)
        p = existente
        p.write({'categ_id': cat_cel.id, 'tracking': 'lot'})
    else:
        p = env['product.template'].create({
            'name': nombre,
            'default_code': codigo,
            'categ_id': cat_cel.id,
            'tracking': 'lot',
            'type': 'consu',
            'purchase_ok': True,
            'sale_ok': False,
        })
        print("[%s] CREADO: %s" % (codigo, nombre))

    p.amunet_lot_prefix = prefijo
    print("  → prefijo: %s | seq: %s | ejemplo: %s" % (
        prefijo,
        p.lot_sequence_id.name if p.lot_sequence_id else 'ERROR',
        p.next_serial or '(al recibir)'
    ))

env.cr.commit()
print("\nCOMMIT OK")
