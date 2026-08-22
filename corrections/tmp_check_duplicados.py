terminos = ['calprotectina', 'NT-proBNP', 'proBNP']
for term in terminos:
    prods = env['product.template'].with_context(active_test=False).search([
        ('name', 'ilike', term)
    ], order='id')
    if prods:
        print(f"\n=== '{term}' ({len(prods)} resultado/s) ===")
        for p in prods:
            print(f"  id={p.id} [{p.default_code or 'SIN CÓDIGO'}] '{p.name}' | tipo={p.type} | activo={p.active} | creado={str(p.create_date)[:10]} | categ={p.categ_id.complete_name}")
