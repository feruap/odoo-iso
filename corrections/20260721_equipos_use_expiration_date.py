"""
Activa use_expiration_date en equipos grandes (tracking=lot, no refacciones EQREF*).
Instrucción de Calidad: la caducidad/vigencia es obligatoria al recibir estos equipos.
Acepta fecha real o la palabra "vigente".
"""
codigos = [
    'EQAMC01',  # Agitador magnético
    'EQBSD01',  # Balanza semianalítica
    'EQCBV01',  # Centrífuga de baja velocidad
    'EQEPV01',  # Autoclave
    'EQINC01',  # Incubadora
    'EQRMA01',  # Recuperador magnético
    'EQTER01',  # Termobloque MDB100
    'EQTER02',  # Termobloque DB100
    'EQVOR01',  # Vortex
    'AMU-83672',  # Laboratorio portable inicial
]

prods = env['product.template'].with_context(active_test=False).search([
    ('default_code', 'in', codigos)
])

print(f"Productos encontrados: {len(prods)} de {len(codigos)}")
for p in prods:
    p.sudo().write({'use_expiration_date': True})
    print(f"  [{p.default_code}] {p.name} → use_expiration_date=True")

faltantes = set(codigos) - set(prods.mapped('default_code'))
if faltantes:
    print(f"\nNo encontrados: {faltantes}")

env.cr.commit()
print("\n✓ Listo")
