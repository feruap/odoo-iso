for term in ['esponja', 'almohadilla fibra', 'probeta 250']:
    prods = env['product.template'].with_context(active_test=False).search([
        ('name', 'ilike', term)
    ], order='id')
    print(f"\n=== '{term}' ({len(prods)}) ===")
    for p in prods:
        print(f"  id={p.id} [{p.default_code or 'SIN CÓDIGO'}] '{p.name}' | activo={p.active} | categ={p.categ_id.complete_name} | creado={str(p.create_date)[:10]}")
