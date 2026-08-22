# El BoM de TIFOIDEA DMTIF01 tenia product_qty=70 (era "para 70 piezas"), asi que
# las cantidades por linea quedaban divididas entre 70. Debe ser 1 (por pieza), igual
# que COVID DIAM-023. Las lineas ya estan correctas por pieza. Autorizado Fernando 2026-07-23.
t = env['product.template'].sudo().search([('default_code', '=', 'DMTIF01')], limit=1)
bom = env['mrp.bom'].sudo().with_context(active_test=False).search([('product_tmpl_id', '=', t.id)], limit=1)
assert bom, 'DMTIF01 sin BoM'
print('product_qty antes:', bom.product_qty)
bom.write({'product_qty': 1.0})
env.cr.commit()
print('product_qty despues:', bom.product_qty)
print('LISTO')
