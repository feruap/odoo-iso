# Ajustes 2026-07-29 (Fernando): (A) TB solo presentaciones 5 y 20; (B) corregir catalogo
# FAPON de los productos marcados (mover cada codigo a su producto correcto, sin tocar precios);
# (C) renombrar MPANT65/66 a Anti-NT-proBNP. Validado en staging.
# === Tarea A: TB solo presentaciones 5 y 20 ===
tb=env['product.template'].sudo().search([('default_code','=','DMATB01')],limit=1)
pres_del=env['amunet.packaging.presentation'].sudo().search([('product_tmpl_id','=',tb.id),('package_qty','in',[2,10,12])])
env['amunet.packaging.plan.line'].sudo().search([('presentation_id','in',pres_del.ids)]).unlink()
print('TB borrando presentaciones:',sorted(pres_del.mapped('package_qty')))
pres_del.unlink()
print('TB presentaciones ahora:',sorted(env['amunet.packaging.presentation'].sudo().search([('product_tmpl_id','=',tb.id)]).mapped('package_qty')))

# === Tarea B: catalogo FAPON (productos marcados) ===
fapon=env['res.partner'].sudo().search([('name','ilike','fapon')],limit=1)
SET={'MPANT03':'GRCGAMS002','MPANT04':'FPZ0638','MPANT05':'FPZ0639','MPANT16':'BENVDN104',
     'MPANT22':'BRCINFS104','MPANT23':'BRNINFC201','MPANT30':'BRNINFJ204','MPANT31':'BRCINFS102',
     'MPANT38':'FPZ0180','MPANT39':'FPZ0181','MPANT65':'BNCBNPN128','MPANT66':'BRJNBNPS103'}
QUITA=['MPANT01','MPANT02']
SI=env['product.supplierinfo'].sudo()
# Pass 1: limpiar cada codigo destino de donde este (evita duplicado). Solo product_code, NO precios.
for code in set(SET.values()):
    SI.search([('partner_id','=',fapon.id),('product_code','=',code)]).write({'product_code':False})
# Pass 2: poner el codigo correcto en su producto (actualiza linea existente = conserva precio; crea si no hay)
for pcode,code in SET.items():
    p=env['product.template'].sudo().search([('default_code','=',pcode)],limit=1)
    lines=SI.search([('product_tmpl_id','=',p.id),('partner_id','=',fapon.id)])
    if lines: lines[0].product_code=code
    else: SI.create({'partner_id':fapon.id,'product_tmpl_id':p.id,'product_code':code})
# Pass 3: quitar clave proveedor
for pcode in QUITA:
    p=env['product.template'].sudo().search([('default_code','=',pcode)],limit=1)
    SI.search([('product_tmpl_id','=',p.id),('partner_id','=',fapon.id)]).write({'product_code':False})

# === Tarea C: renombrar MPANT65/66 ===
REN={'MPANT65':'Anticuerpo de captura Anti-NT-proBNP','MPANT66':'Anticuerpo de detección Anti-NT-proBNP'}
for pcode,nn in REN.items():
    p=env['product.template'].sudo().search([('default_code','=',pcode)],limit=1)
    p.with_context(lang='en_US').write({'name':nn})
    p.with_context(lang='es_MX').write({'name':nn})
env.cr.commit()

# verificacion FAPON
print('--- FAPON despues (marcados) ---')
for pcode in list(SET)+QUITA:
    p=env['product.template'].sudo().search([('default_code','=',pcode)],limit=1)
    c=SI.search([('product_tmpl_id','=',p.id),('partner_id','=',fapon.id)]).mapped('product_code')
    print(' ',pcode,p.with_context(lang='es_MX').name[:40],'->',c)
print('AJUSTES3_OK')
