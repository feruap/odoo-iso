prods = env['product.template'].with_context(active_test=False).search([
    ('default_code', 'like', 'MPREC%')
], order='default_code')
print(f"{'Clave':<16} {'Nombre'}")
print("-"*75)
for p in prods:
    print(f"{p.default_code:<16} {p.name}")
print(f"\nTotal: {len(prods)} productos")
