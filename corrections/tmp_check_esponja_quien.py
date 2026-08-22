prods = env['product.template'].with_context(active_test=False).search([
    ('name', 'ilike', 'esponja')
], order='id')
for p in prods:
    usuario = p.create_uid
    print(f"id={p.id} [{p.default_code}] creado={str(p.create_date)[:16]} | por: {usuario.name} ({usuario.login})")
