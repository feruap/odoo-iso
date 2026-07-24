faltantes = [46, 48, 50, 51, 52, 53, 55, 56, 65, 66, 67, 70, 73, 74, 79, 80, 82, 89]
print("Verificando huecos en producción:\n")
for n in faltantes:
    codigo = f'MPREC{n}'
    p = env['product.template'].with_context(active_test=False).search([
        ('default_code', '=', codigo)
    ], limit=1)
    if p:
        print(f"  ✅ {codigo} — {p.name}")
    else:
        print(f"  ❌ {codigo} — NO EXISTE")
