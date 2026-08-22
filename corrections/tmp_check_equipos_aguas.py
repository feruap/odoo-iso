# Equipos
equipos = env['product.template'].search([
    ('categ_id.complete_name', 'ilike', 'equipo')
], order='default_code')
print(f"=== EQUIPOS ({len(equipos)}) ===")
for p in equipos:
    print(f"  [{p.default_code}] {p.name} | use_exp={p.use_expiration_date} | tracking={p.tracking}")

# Aguas
aguas = env['product.template'].search([
    '|', '|',
    ('name', 'ilike', 'agua destilada'),
    ('name', 'ilike', 'agua bidestilada'),
    ('name', 'ilike', 'agua tridestilada'),
], order='default_code')
print(f"\n=== AGUAS ({len(aguas)}) ===")
for p in aguas:
    print(f"  [{p.default_code}] {p.name} | use_exp={p.use_expiration_date} | tracking={p.tracking} | categ={p.categ_id.complete_name}")
