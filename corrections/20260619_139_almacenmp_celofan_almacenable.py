# Activar is_storable=True en los 3 productos de Consumible/Celofán
# Fueron creados con type='consu' pero sin is_storable, quedando como consumibles
# puros (sin inventario). La corrección los hace almacenables conservando type='consu'
# para que sigan visibles en el filtro "Bienes" de la vista de productos.

codigos = ['COBCE01', 'COBCE02', 'COBCE03']

for codigo in codigos:
    pt = env['product.template'].search([('default_code', '=', codigo)], limit=1)
    if not pt:
        print("[%s] NO ENCONTRADO — omitiendo" % codigo)
        continue

    antes = pt.is_storable
    pt.write({'is_storable': True})
    despues = pt.is_storable
    print("[%s] %s | is_storable: %s → %s" % (
        codigo,
        pt.name or '(sin nombre)',
        antes,
        despues,
    ))

env.cr.commit()
print("\nCOMMIT OK")
