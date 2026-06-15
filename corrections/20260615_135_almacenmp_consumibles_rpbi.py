# Crear categoría Consumible/RPBI y sus tres productos con secuencia de lote

# ─── 1. Categoría ────────────────────────────────────────────────────────────
cat_padre = env['product.category'].search([('name', '=', 'Consumible')], limit=1)
if not cat_padre:
    cat_padre = env['product.category'].search([('name', 'ilike', 'Consumible')], limit=1)
print("Categoría padre: [%d] %s" % (cat_padre.id, cat_padre.name))

cat_rpbi = env['product.category'].search([
    ('name', '=', 'RPBI'), ('parent_id', '=', cat_padre.id)
], limit=1)
if not cat_rpbi:
    cat_rpbi = env['product.category'].create({
        'name': 'RPBI',
        'parent_id': cat_padre.id,
    })
    print("Categoría CREADA: %s" % cat_rpbi.complete_name)
else:
    print("Categoría ya existía: %s" % cat_rpbi.complete_name)

# ─── 2. Productos ─────────────────────────────────────────────────────────────
productos_def = [
    ('COBRP01', 'Bolsa para RPBI chica',   'BRP01'),
    ('COBRP02', 'Bolsa para RPBI mediana', 'BRP02'),
    ('COBRP03', 'Bolsa para RPBI grande',  'BRP03'),
]

for codigo, nombre, prefijo in productos_def:
    existente = env['product.template'].search([('default_code', '=', codigo)], limit=1)
    if existente:
        print("[%s] Ya existía — actualizando" % codigo)
        p = existente
        p.write({'categ_id': cat_rpbi.id, 'tracking': 'lot'})
    else:
        p = env['product.template'].create({
            'name': nombre,
            'default_code': codigo,
            'categ_id': cat_rpbi.id,
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
        p.next_serial if p.next_serial else '(calcular al recibir)'
    ))

env.cr.commit()
print("\nCOMMIT OK")
