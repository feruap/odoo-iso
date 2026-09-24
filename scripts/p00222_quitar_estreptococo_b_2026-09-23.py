# P00222: se quitan los dos renglones de Estreptococo B.
#
# El reporte de temporada del 19-sep-2026 marcaba Estreptococo A (DMSPN02,
# 147/mes, 5.4 meses, ATENCION). Estreptococo B (DMSPN01) NO aparece ni una vez
# en ese reporte: ni el producto, ni su hoja SPHMC51. Al dia siguiente la orden
# se armo con la hoja y los cartuchos del B, justificados con "de 20 a 580 pzs",
# cifra que no existe en ninguna fuente.
#
# Dato real, contado desde los pedidos de la tienda (1,200 pedidos, 12 meses):
#   DMSPN01 Estreptococo B   12 cajas de 20  =   240 pz/ano  = 20/mes
#   DMSPN02 Estreptococo A   21x5 + 22x20    =   545 pz/ano  = 45/mes
# Con 320 pz de B en almacen, son 16 meses de cobertura. Las 9 hojas rendirian
# ~900 pruebas mas, o sea 45 meses adicionales.
#
# Detectado por Fernando el 23-sep. La orden esta en borrador y sin recibir.
CLAVES = ['SPHMC51', 'MPCAR51']
PO = env['purchase.order'].search([('name', '=', 'P00222')], limit=1)
assert PO, 'No existe P00222'
assert PO.state == 'draft', 'P00222 ya no esta en borrador (%s), no se toca' % PO.state

quitadas, importe = [], 0.0
for l in PO.order_line:
    cod = l.product_id.default_code
    if cod in CLAVES:
        quitadas.append('%s x%s a %s = %.2f %s' % (cod, l.product_qty, l.price_unit,
                                                   l.price_subtotal, PO.currency_id.name))
        importe += l.price_subtotal
        l.unlink()

PO.message_post(body=(
    'Se quitan los renglones de <b>Estreptococo B</b> (SPHMC51 y MPCAR51) por '
    '%.2f %s.<br/><br/>El reporte de temporada del 19-sep marcaba Estreptococo '
    '<b>A</b> (DMSPN02), no el B: el B no aparece ni una vez en ese reporte. '
    'Contado desde los pedidos de la tienda, el B vende 240 piezas al año y hay '
    '320 en almacén: 16 meses de cobertura. La justificación original decía '
    '"de 20 a 580 pzs", cifra que no existe en ninguna fuente.<br/><br/>'
    'Detectado por Fernando, 23-sep-2026.') % (importe, PO.currency_id.name))
env.cr.commit()
print('renglones quitados:')
for q in quitadas: print('   %s' % q)
print('importe liberado: %.2f %s' % (importe, PO.currency_id.name))
PO.invalidate_recordset()
print('\nP00222 queda con %s renglones, total %.2f %s' % (len(PO.order_line), PO.amount_total, PO.currency_id.name))
