"""Nanoparticulas: el citrato de sodio 1% pasa de 10 a 15 ml.

Pedido de Mery, 24-sep-2026. Acompana al cambio de codigo que renombra la
columna "Tamano (nm)" de la tabla de reacciones a "D.O.".

La receta SPNPS01 produce 0.70 L y lleva:
    SPCDS01 Citrato de sodio 1%      10 -> 15 ml
    SPACL01 Acido cloroaurico 1%     10 ml (sin cambio)
    MPATR01 Agua tridestilada        0.049 garrafones (sin cambio)

Nota sobre el agua: se mide en GARRAFONES, no en litros. 0.05 de garrafon por
litro de solucion, o sea garrafones de 20 L. Todas las soluciones lo usan asi;
el 0.049 parece un error y no lo es.

PENDIENTE de confirmar con Mery: el rendimiento sigue en 0.70 L. Si subir el
citrato hace que rinda mas, hay que ajustarlo tambien.
"""

"""Nanoparticulas: el citrato de sodio 1% pasa de 10 a 15 ml.

Pedido de Mery, 24-sep-2026.
"""
bom = env['mrp.bom'].search([('product_tmpl_id.default_code','=','SPNPS01')], limit=1)
assert bom, 'no existe la receta de SPNPS01'
cit = env['product.product'].search([('default_code','=','SPCDS01')], limit=1)
linea = bom.bom_line_ids.filtered(lambda l: l.product_id == cit)
assert linea, 'la receta no lleva SPCDS01'
print('receta %s: produce %s %s' % (bom.id, bom.product_qty, bom.product_uom_id.name))
print('ANTES:')
for l in bom.bom_line_ids:
    print('   %-9s %8.4f %s' % (l.product_id.default_code, l.product_qty, l.product_uom_id.name))
antes = linea.product_qty
linea.write({'product_qty': 15.0})
bom.product_tmpl_id.message_post(body=(
    'Receta ajustada el 24-sep-2026: el <b>Citrato de sodio 1{pc} (SPCDS01)</b> '
    'pasa de {antes} a <b>15 ml</b> por cada {prod} {uom} de solucion. '
    'Pedido de Mery.'
).format(pc='%', antes=antes, prod=bom.product_qty, uom=bom.product_uom_id.name))
env.cr.commit()
print('DESPUES:')
for l in bom.bom_line_ids:
    print('   %-9s %8.4f %s' % (l.product_id.default_code, l.product_qty, l.product_uom_id.name))
