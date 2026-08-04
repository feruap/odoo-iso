"""Busca Combo Mosquito / CAC11 en producción."""
# Por código
r1 = env['product.template'].with_context(active_test=False).search([
    ('default_code', 'ilike', 'CAC11')], limit=5)
print(f"Por código 'CAC11': {len(r1)}")
for t in r1:
    print(f"  [{t.default_code}] {t.name} | tracking={t.tracking}")

# Por nombre
r2 = env['product.template'].with_context(active_test=False).search([
    ('name', 'ilike', 'mosquito')], limit=5)
print(f"\nPor nombre 'mosquito': {len(r2)}")
for t in r2:
    print(f"  [{t.default_code}] {t.name} | tracking={t.tracking}")

# Por nombre combo
r3 = env['product.template'].with_context(active_test=False).search([
    ('name', 'ilike', 'combo')], limit=10)
print(f"\nPor nombre 'combo' (muestra): {len(r3)}")
for t in r3:
    print(f"  [{t.default_code}] {t.name} | tracking={t.tracking}")
