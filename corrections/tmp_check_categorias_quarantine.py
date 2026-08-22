# Ver qué categorías tienen quarantine=True (son las que mandan los MP a Control de calidad)
cats = env['product.category'].search([('amunet_requires_quarantine', '=', True)])
print(f"Categorías con quarantine=True: {len(cats)}")
for c in cats:
    n_prods = env['product.template'].search_count([('categ_id', '=', c.id)])
    print(f"  [{c.id}] {c.complete_name} | {n_prods} productos")

print()
# MP que sí requieren cuarentena (por producto o categoría)
mp = env['product.template'].search([('default_code', 'like', 'MP%')])
requieren = [p for p in mp if p._amunet_effective_requires_quarantine()]
no_requieren = [p for p in mp if not p._amunet_effective_requires_quarantine()]
print(f"Materia prima (MP*): {len(mp)} total")
print(f"  Con cuarentena: {len(requieren)}")
print(f"  Sin cuarentena: {len(no_requieren)}")
if no_requieren[:5]:
    print("  Primeros sin cuarentena (verificar si es correcto):")
    for p in no_requieren[:10]:
        print(f"    [{p.default_code}] {p.name}")
