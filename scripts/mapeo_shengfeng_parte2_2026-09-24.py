# Segunda tanda del mapeo ShengFeng. Todo verificado contra el catalogo del
# proveedor (en.shengfengpack.com), leyendo el HTML porque el sitio no entrega
# las tablas de otro modo:
#
#   ficha 742 (Disposable dropper 1):  DG013 | XC-4 | 10 ul | PE | 61 mm
#   ficha 743 (Disposable dropper 2):  DG005 | AD-5 | 25 ul | PE | 80 mm
#   ficha 678 (Pipette Tip 200ul):     800201 | 200 ul | PP | 7.3*50.2 mm
#
# 25 ul aparece UNA sola vez en todo su catalogo de goteros: el DG005. Nuestro
# STGOT04 se llama "Gotero de 25 ul", asi que no hay otro candidato posible.
# (Fernando habia propuesto STGOT05 de 40 ul o STGOT02 de 5 ul; el catalogo
# descarta los dos.)
#
# Las puntas amarillas de 200 ul son color estandar de esa capacidad.

PROV = 'Cangzhou ShengFeng Plastic Product Co., Ltd.'

MAPEO = [
    ('STGOT04', 'DG005',  'DG005 / Transfer pipette AD-5, clear color, 25ul, 80mm'),
    ('COPUN03', '800201', '800201 / Pipette tip 200ul, PP, 7.3*50.2mm, yellow'),
]

S = env['product.supplierinfo']
T = env['product.template']
prov = env['res.partner'].search([('name', '=', PROV)], limit=1)
assert prov, 'No existe el proveedor'

for clave, codigo, nombre in MAPEO:
    t = T.search([('default_code', '=', clave)], limit=1)
    assert t, 'No existe %s' % clave
    lineas = S.search([('product_tmpl_id', '=', t.id), ('partner_id', '=', prov.id)])
    if not lineas:
        S.create({'product_tmpl_id': t.id, 'partner_id': prov.id,
                  'product_code': codigo, 'product_name': nombre})
        print('  +  %-9s %-7s creado' % (clave, codigo))
    else:
        lineas[0].write({'product_code': codigo, 'product_name': nombre})
        print('  ~  %-9s %-7s actualizado' % (clave, codigo))

env.cr.commit()

print('\n=== P00226 COMO LO VERA SHENGFENG ===')
po = env['purchase.order'].search([('name', '=', 'P00226')], limit=1)
faltan = []
for lin in po.order_line:
    t = lin.product_id.product_tmpl_id
    si = S.search([('product_tmpl_id', '=', t.id), ('partner_id', '=', prov.id)], limit=1)
    if si and si.product_code:
        print('  %-9s %-7s %-6.0f  %s' % (t.default_code, si.product_code,
                                          lin.product_qty, si.product_name))
    else:
        faltan.append(t.default_code)
        print('  %-9s %-7s %-6.0f  %s' % (t.default_code, '--FALTA--',
                                          lin.product_qty, t.default_code))
print('\nsin codigo: %s' % (', '.join(faltan) if faltan else 'ninguno'))

print('\n=== TODOS LOS GOTEROS CONTRA EL CATALOGO DE SHENGFENG ===')
for cod in ['STGOT01','STGOT02','STGOT03','STGOT04','STGOT05','STGOT06','STGOT07']:
    tt = T.search([('default_code', '=', cod)], limit=1)
    si = S.search([('product_tmpl_id', '=', tt.id), ('partner_id', '=', prov.id)], limit=1)
    print('  %-9s %-28s -> %s' % (cod, (tt.name or '')[:28],
                                  (si.product_code if si and si.product_code else 'sin mapear')))
