p = env['product.template'].search([('default_code','=','MPREC19')], limit=1)
p.sudo().write({'name': 'Ácido fosfórico'})
env.cr.commit()
print(f"[{p.default_code}] → {p.name} ✓")
