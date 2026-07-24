"""Activa cuarentena en todos los equipos con rastreo de lote (excluye refacciones)."""
equipos = env['product.template'].with_context(active_test=False).search([
    ('default_code', 'like', 'EQ%'),
    ('tracking', '!=', 'none'),
])
# También el laboratorio portable
lab = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'AMU-83672')
], limit=1)
todos = equipos | lab

for p in todos:
    if not p.amunet_requires_quarantine:
        p.sudo().write({'amunet_requires_quarantine': True})
        print(f"  [{p.default_code}] {p.name[:50]} → cuarentena activada")
    else:
        print(f"  [{p.default_code}] {p.name[:50]} → ya tenía cuarentena")

env.cr.commit()
print(f"\n✓ {len(todos)} equipos revisados")
