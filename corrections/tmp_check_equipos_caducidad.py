codigos = ['EQAMC01','EQBSD01','EQCBV01','EQEPV01','EQINC01',
           'EQRMA01','EQTER01','EQTER02','EQVOR01','AMU-83672','EQBAD01',
           'EQREF01','EQREF02','EQREF03','EQREF04','EQREF05',
           'EQREF06','EQREF07','EQREF08','EQREF09','EQTRV01']
prods = env['product.template'].with_context(active_test=False).search([
    ('default_code','in',codigos)
], order='default_code')
print(f"{'Código':<12} {'Nombre':<35} {'Caducidad':>9} {'Rastreo':>8}")
print("-"*70)
for p in prods:
    print(f"{p.default_code or '':<12} {p.name[:35]:<35} {str(p.use_expiration_date):>9} {p.tracking:>8}")
