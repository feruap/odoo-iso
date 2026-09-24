# YP001 de Cangzhou ShengFeng quedo cargado con la descripcion "CRYOVIAL TUBE",
# sin volumen. Los otros dos crioviales si lo traen, y el PDF que se le manda al
# proveedor sale de este campo: sin volumen, ShengFeng no sabe cual de los
# cuatro de su linea BLK le estamos pidiendo.
#
# Se completa con la referencia exacta de SU catalogo (shengfengpack.com):
#   BLK-0.5ML  BLK-0.8ML  BLK-1.0ML  BLK-1.5ML   son CUATRO productos distintos
#
# El nuestro es el de 0.8: confirmado por Mery fisicamente, y por la foto de la
# ficha del proveedor (el 0.8 es corto y ancho con fondo plano; el 1.0 es mas
# largo, estrecho y de fondo conico, que no corresponde al nuestro).
CLAVE = 'COCRI02'
CODIGO = 'YP001'
NUEVO = 'BLK-0.8ML Cryovial tube 0.8ml - green cap, clear tube'

S = env['product.supplierinfo']
t = env['product.template'].search([('default_code', '=', CLAVE)], limit=1)
assert t, 'No existe %s' % CLAVE
linea = S.search([('product_tmpl_id', '=', t.id), ('product_code', '=', CODIGO)])
assert len(linea) == 1, 'Se esperaba UN renglon %s, hay %s' % (CODIGO, len(linea))
print('antes : %s -> %r' % (CODIGO, linea.product_name))
linea.product_name = NUEVO
env.cr.commit()
print('ahora : %s -> %r' % (CODIGO, linea.product_name))

print('\n--- los tres crioviales, como los vera ShengFeng ---')
for cod in ['COCRI01', 'COCRI02', 'COCRI03']:
    tt = env['product.template'].search([('default_code', '=', cod)], limit=1)
    for s in S.search([('product_tmpl_id', '=', tt.id)]):
        if s.product_code:
            print('  %-9s %-8s %s' % (cod, s.product_code, s.product_name))
