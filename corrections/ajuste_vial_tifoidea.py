# Corrige el vial de TIFOIDEA DMTIF01 en sus presentaciones: STBAC01 (sangre/suero/
# plasma) -> STBPR01 (Vial con solucion de corrimiento para pruebas SSP).
# Mismo ajuste que se hizo en COVID DIAM-023. Autorizado por Fernando 2026-07-23.
tif = env['product.template'].sudo().search([('default_code', '=', 'DMTIF01')], limit=1)
bac = env['product.product'].sudo().search([('default_code', '=', 'STBAC01')], limit=1)
bpr = env['product.product'].sudo().search([('default_code', '=', 'STBPR01')], limit=1)
assert tif and bac and bpr, 'falta producto'
comps = env['amunet.packaging.presentation.component'].sudo().search([
    ('presentation_id.product_tmpl_id', '=', tif.id),
    ('product_id', '=', bac.id)])
print('Componentes STBAC01 a cambiar en TIFOIDEA:', len(comps))
comps.write({'product_id': bpr.id})
env.cr.commit()
env.cr.execute("""
  SELECT pr.package_qty, pt.default_code
  FROM amunet_packaging_presentation pr
  JOIN amunet_packaging_presentation_component c ON c.presentation_id=pr.id
  JOIN product_product pp ON pp.id=c.product_id JOIN product_template pt ON pt.id=pp.product_tmpl_id
  WHERE pr.product_tmpl_id=%s AND pt.default_code LIKE 'STB%%' ORDER BY pr.package_qty
""", (tif.id,))
print('Vial en TIFOIDEA ahora:', env.cr.fetchall())
print('LISTO')
