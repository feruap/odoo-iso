terminos = ['mops', 'hepes', 'fosfato de sodio monobásico', 'fosfato de sodio monobasico',
            'peptona', 'caseína', 'metilenbis', 'ácido sulfúrico', 'sulfurico',
            'azul brillante', 'ortosilicato', 'tetraetilo']
vistos = set()
for t in terminos:
    prods = env['product.template'].with_context(active_test=False).search([('name','ilike',t)])
    for p in prods:
        if p.id not in vistos:
            vistos.add(p.id)
            print(f"{p.default_code or '(sin clave)':<16} {p.name}")
