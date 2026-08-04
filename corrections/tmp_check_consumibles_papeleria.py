"""Revisa productos de la categoría Consumibles/Papelería y su convención de claves."""
# Buscar la categoría
categ = env['product.category'].search([
    ('name', 'ilike', 'papeleria')], limit=5)
for c in categ:
    print(f"Categoría: {c.complete_name} (id={c.id})")

print()

# Productos de papelería
prods = env['product.template'].with_context(active_test=False).search([
    ('categ_id.complete_name', 'ilike', 'papeleria')
], order='default_code asc')
print(f"Productos en Papelería: {len(prods)}")
for p in prods:
    print(f"  [{p.default_code}] {p.name}")

print()
# Ver también otros consumibles para entender el patrón general
otros = env['product.template'].with_context(active_test=False).search([
    ('categ_id.complete_name', 'ilike', 'consumible')
], limit=10, order='default_code asc')
print(f"Muestra de otros consumibles (primeros 10):")
for p in otros:
    print(f"  [{p.default_code}] {p.name} — {p.categ_id.complete_name}")
