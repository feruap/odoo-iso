# Solicitud de compra (RFQ) a FAPON de los 13 anticuerpos/antigenos mapeados del
# documento Purchase request 27.07.26. SIN precios (price_unit=0) — solo Fernando
# los captura (restriccion de precios de compras). Falta 1 item: Vitamina D-BSA
# (FPZ0188-3) que no tiene producto en Odoo. Autorizado por Fernando 2026-07-29.
fapon=env['res.partner'].sudo().search([('name','ilike','fapon')],limit=1)
ITEMS=[('MPANT16',4),('MPANT13',5),('MPANT12',5),('MPANT31',5),('MPANT22',10),('MPANT23',16),
       ('MPANT30',7),('MPANT04',20),('MPANT05',7),('MPANT38',5),('MPANT39',10),('MPANT65',2),('MPANT66',2)]
lines=[]
for code,qty in ITEMS:
    p=env['product.product'].sudo().search([('default_code','=',code)],limit=1)
    assert p, 'falta '+code
    lines.append((0,0,{'product_id':p.id,'product_qty':qty,'product_uom_id':p.uom_id.id,'price_unit':0.0,'name':p.name}))
po=env['purchase.order'].sudo().create({'partner_id':fapon.id,'order_line':lines})
po.order_line.write({'price_unit':0.0})
env.cr.commit()
print('RFQ creada:', po.name, '| proveedor:', po.partner_id.name, '| lineas:', len(po.order_line), '| estado:', po.state)
print('precios en 0 (sin exponer):', all(l.price_unit==0.0 for l in po.order_line))
print('LISTO')
