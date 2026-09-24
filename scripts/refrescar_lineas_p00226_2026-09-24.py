# El texto de cada renglon de una orden de compra (purchase.order.line.name) se
# congela cuando se crea el renglon. P00226 se armo ANTES de cargar las claves
# de ShengFeng, asi que el PDF sigue saliendo con nuestras claves internas
# ([MPCAR07] Cartucho Hemoglobina), que es justo lo que Ron no puede usar:
# el no vende "Cartucho Hemoglobina", vende molde K007 con impresion "HbA1c".
#
# Se reescribe SOLO el campo name (texto descriptivo). No se tocan cantidades,
# precios, fechas ni el estado de la orden.
#
# Formato: primero lo que ShengFeng necesita para fabricarlo, y debajo nuestra
# clave entre parentesis para no perder la trazabilidad de nuestro lado.

PROV = 'Cangzhou ShengFeng Plastic Product Co., Ltd.'
ORDEN = 'P00226'

S = env['product.supplierinfo']
po = env['purchase.order'].search([('name', '=', ORDEN)], limit=1)
assert po, 'no existe %s' % ORDEN
prov = po.partner_id
assert prov.name == PROV, 'la orden no es de ShengFeng'

sin_codigo = []
for l in po.order_line:
    t = l.product_id.product_tmpl_id
    si = S.search([('product_tmpl_id', '=', t.id), ('partner_id', '=', prov.id)], limit=1)
    interno = '%s %s' % (t.default_code, t.name)
    if si and si.product_code:
        nuevo = '%s\n(Amunet: %s)' % (si.product_name or si.product_code, interno)
    else:
        sin_codigo.append(t.default_code)
        nuevo = '%s\n(pendiente de clave ShengFeng)' % interno
    antes = (l.name or '').replace('\n', ' / ')
    l.name = nuevo
    print('  %-9s' % t.default_code)
    print('      antes: %s' % antes[:88])
    print('      ahora: %s' % nuevo.replace('\n', ' / ')[:88])

env.cr.commit()
print('\nrenglones sin clave de ShengFeng: %s'
      % (', '.join(sin_codigo) if sin_codigo else 'ninguno'))
