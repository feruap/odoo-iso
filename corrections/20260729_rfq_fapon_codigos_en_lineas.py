# Agrega el codigo de proveedor FAPON al inicio de la descripcion de cada linea
# de la RFQ P00197 (formato "[CODIGO] nombre") para que FAPON identifique los
# productos al cotizar. NO toca precios. Autorizado por Fernando 2026-07-29.
po=env['purchase.order'].sudo().search([('name','=','P00197')],limit=1)
assert po, 'P00197 no existe'
SI=env['product.supplierinfo'].sudo()
n=0
for line in po.order_line:
    si=SI.search([('product_tmpl_id','=',line.product_id.product_tmpl_id.id),
                  ('partner_id','=',po.partner_id.id),('product_code','!=',False)],limit=1)
    if si and not (line.name or '').startswith('['):
        line.name='[%s] %s' % (si.product_code, line.name or line.product_id.name)
        n+=1
env.cr.commit()
print('lineas actualizadas con codigo FAPON:', n)
for l in po.order_line:
    print('  ', l.name)
print('LISTO')
