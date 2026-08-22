from collections import defaultdict

# Buscar todos los product.template activos con código
todos = env['product.template'].with_context(active_test=False).search(
    [('default_code', '!=', False)], order='name, id'
)

# Agrupar por nombre normalizado (sin espacios extra, minúsculas)
por_nombre = defaultdict(list)
for p in todos:
    clave = p.name.strip().lower()
    por_nombre[clave].append(p)

print("=== DUPLICADOS POR NOMBRE EXACTO ===")
encontrados = 0
for nombre, prods in sorted(por_nombre.items()):
    if len(prods) > 1:
        encontrados += 1
        print(f"\n'{prods[0].name}'")
        for p in prods:
            print(f"  [{p.default_code}] activo={p.active} categ={p.categ_id.complete_name} creado={str(p.create_date)[:10]}")

print(f"\nTotal de nombres con duplicados: {encontrados}")
