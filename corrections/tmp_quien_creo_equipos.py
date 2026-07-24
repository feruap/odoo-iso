equipos = env['product.template'].with_context(active_test=False).search([
    ('default_code', 'like', 'EQ%')
], order='default_code')

print(f"{'Código':<12} {'Nombre':<40} {'Creado por':<30} {'Fecha'}")
print("-"*105)
for p in equipos:
    usuario = p.create_uid.name if p.create_uid else '(desconocido)'
    fecha = p.create_date.strftime('%Y-%m-%d') if p.create_date else '---'
    print(f"{p.default_code or '':<12} {p.name[:40]:<40} {usuario:<30} {fecha}")
