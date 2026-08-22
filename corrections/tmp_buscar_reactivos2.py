nombres = [
    'ferric', 'hierro', 'molibdeno', 'molibdato', 'dextrosa',
    'agarosa', 'etilenglicol', 'etilengl', 'imidazol', 'amarillo'
]
vistos = set()
for n in nombres:
    prods = env['product.template'].with_context(active_test=False).search([
        ('name', 'ilike', n)
    ])
    for p in prods:
        if p.id not in vistos:
            vistos.add(p.id)
            print(f"{p.default_code or '(sin clave)':<16} {p.name[:60]}")
# Buscar también por clave MPREC completa para ver todos
todos = env['product.template'].with_context(active_test=False).search([
    ('default_code', 'like', 'MPREC%')
], order='default_code')
print("\n--- Todos los MPREC ---")
for p in todos:
    print(f"{p.default_code:<16} {p.name[:60]}")
