# Ajusta las presentaciones de TIFOIDEA DMTIF01: deben ser 5 y 20 pzas por caja
# (estaban en 2 y 20). Se cambia la de package_qty=2 -> 5. Autorizado Fernando 2026-07-23.
t = env['product.template'].sudo().search([('default_code', '=', 'DMTIF01')], limit=1)
Pres = env['amunet.packaging.presentation'].sudo()
p2 = Pres.search([('product_tmpl_id', '=', t.id), ('package_qty', '=', 2)], limit=1)
assert p2, 'no hay presentacion de 2 en TIFOIDEA'
p2.write({'package_qty': 5, 'name': 'Caja con 5 pruebas'})
env.cr.commit()
res = Pres.search([('product_tmpl_id', '=', t.id)]).mapped('package_qty')
print('Presentaciones TIFOIDEA ahora:', sorted(res))
print('LISTO')
