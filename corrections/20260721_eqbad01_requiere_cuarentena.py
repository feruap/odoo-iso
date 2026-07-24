p = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'EQBAD01')
], limit=1)
p.sudo().write({'amunet_requires_quarantine': True})
env.cr.commit()
print(f"[{p.default_code}] {p.name} → amunet_requires_quarantine=True ✓")
