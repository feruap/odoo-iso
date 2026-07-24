p = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'EQTRV01')
], limit=1)
p.sudo().write({'use_expiration_date': True})
env.cr.commit()
print(f"[{p.default_code}] {p.name} → use_expiration_date=True ✓")
