nombres = [
    'tris', 'cloruro f', 'molibdato', 'molibato', 'tween',
    'agar dextrosa', 'papa', 'agarosa', 'glicina', 'fosfor',
    'etilenglicol', 'imidazol', 'clorhidrico', 'colorante amarillo'
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
