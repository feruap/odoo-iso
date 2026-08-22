terminos = ['cloruro de calcio', 'sulfato de magnesio', 'acetato de magnesio',
            'aminoacético', 'aminoacetico', 'glicina', 'hidroxido de sodio', 'hidróxido de sodio']
vistos = set()
for t in terminos:
    prods = env['product.template'].with_context(active_test=False).search([('name','ilike',t)])
    for p in prods:
        if p.id not in vistos:
            vistos.add(p.id)
            print(f"{p.default_code or '(sin clave)':<16} {p.name}")
