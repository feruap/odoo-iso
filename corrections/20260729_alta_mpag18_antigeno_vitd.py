# Alta del antigeno faltante Vitamina D-BSA como MPAG18 (siguiente clave libre;
# MPAG01-17 consecutivos). Config copiada de MPAG02 (uom mg, categoria Antigeno
# recombinante, tracking lote). Codigo de proveedor FAPON FPZ0188-3 (SIN precio).
# Se agrega a la RFQ P00197 (5 mg, precio 0). Autorizado por Fernando 2026-07-29.
ref=env['product.template'].sudo().search([('default_code','=','MPAG02')],limit=1)
assert ref, 'MPAG02 referencia no existe'
assert not env['product.template'].sudo().search([('default_code','=','MPAG18')]), 'MPAG18 ya existe'
vals={'name':'Antígeno Vitamina D-BSA','default_code':'MPAG18','type':ref.type,
      'categ_id':ref.categ_id.id,'uom_id':ref.uom_id.id,
      'tracking':'lot','purchase_ok':True,'sale_ok':False,'amunet_lot_prefix':'AG18'}
tmpl=env['product.template'].sudo().with_context(amunet_alta_autorizada=True).create(vals)
if 'is_storable' in tmpl._fields: tmpl.sudo().write({'is_storable':ref.is_storable})
fapon=env['res.partner'].sudo().search([('name','ilike','fapon')],limit=1)
env['product.supplierinfo'].sudo().create({'partner_id':fapon.id,'product_tmpl_id':tmpl.id,'product_code':'FPZ0188-3'})
print('creado', tmpl.default_code, tmpl.name, '| uom', tmpl.uom_id.name, '| lot_prefix', tmpl.amunet_lot_prefix)
# agregar a la RFQ P00197
po=env['purchase.order'].sudo().search([('name','=','P00197')],limit=1)
if po:
    env['purchase.order.line'].sudo().create({'order_id':po.id,'product_id':tmpl.product_variant_id.id,
        'product_qty':5,'product_uom_id':tmpl.uom_id.id,'price_unit':0.0,'name':tmpl.name})
    po.order_line.write({'price_unit':0.0})
    print('agregado a', po.name, '| lineas ahora:', len(po.order_line), '| todo precio 0:', all(l.price_unit==0.0 for l in po.order_line))
env.cr.commit()
print('LISTO')
