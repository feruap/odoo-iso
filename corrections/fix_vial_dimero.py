tmpl = env['product.template'].search([('default_code','=','DMDMD01')], limit=1)
stbac = env['product.product'].search([('default_code','=','STBAC01')], limit=1)
stbpr = env['product.product'].search([('default_code','=','STBPR01')], limit=1)
assert stbpr, 'no existe STBPR01'
n = 0
for pres in env['amunet.packaging.presentation'].search([('product_tmpl_id','=',tmpl.id)]):
    for comp in pres.component_ids:
        if comp.product_id.id == stbac.id:
            comp.product_id = stbpr.id
            n += 1
env.cr.commit()
print('componentes cambiados STBAC01->STBPR01:', n)
for pres in env['amunet.packaging.presentation'].search([('product_tmpl_id','=',tmpl.id)]).sorted('package_qty'):
    print(' presentacion', pres.package_qty, ':', [c.product_id.default_code for c in pres.component_ids])
