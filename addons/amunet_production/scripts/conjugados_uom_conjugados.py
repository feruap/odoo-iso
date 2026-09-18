# Conjugados: la unidad pasa de Litros a Mililitros (una tanda son decimas de mL)
ml = env['uom.uom'].browse(11)
tmpls = env['product.template'].search([('default_code', 'like', 'SPCDE%')], order='default_code')
print('Productos: %s  | unidad destino: %s' % (len(tmpls), ml.name))
movs = env['stock.move'].search_count([('product_id.product_tmpl_id', 'in', tmpls.ids)])
if movs:
    print('ABORTADO: hay %s movimientos, no se cambia la unidad' % movs)
else:
    tmpls.write({'uom_id': ml.id})
    env.cr.commit()
    print('COMMIT OK - %s productos ahora en %s' % (len(tmpls), ml.name))
