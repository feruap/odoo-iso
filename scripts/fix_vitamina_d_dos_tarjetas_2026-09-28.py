# -*- coding: utf-8 -*-
"""Vitamina D (SPHMC09) quedo con DOS tarjetas de soporte.

Produccion tenia MPTS01 (6x30 cm) desde antes. El archivo de Mery dice que
Vitamina D es la unica que usa MPTS02 (8x30 cm), asi que al cargar la linea de
laminado se agrego la de 8 y quedaron las dos: la hoja pediria dos tarjetas por
cada 30 cm producidos.

Se quita la de 6x30 y se queda la de 8x30, que es la que indica el archivo.

En staging no paso: alli la receta se armo de cero con MPTS02.
"""
P = env['product.product'].sudo()
p = P.search([('default_code','=','SPHMC09')], limit=1)
bom = env['mrp.bom'].sudo().search([('product_tmpl_id','=',p.product_tmpl_id.id)], limit=1)
t01 = [l for l in bom.bom_line_ids if l.product_id.default_code == 'MPTS01']
t02 = [l for l in bom.bom_line_ids if l.product_id.default_code == 'MPTS02']
print('   antes: %s lineas   MPTS01=%s  MPTS02=%s' % (len(bom.bom_line_ids), len(t01), len(t02)))
if t01 and t02:
    for l in t01:
        print('      quitando %s (%s)' % (l.product_id.default_code, l.product_id.name))
        l.unlink()
    bom.invalidate_recordset()
    print('   despues: %s lineas' % len(bom.bom_line_ids))
elif t01 and not t02:
    print('   OJO: solo tiene la de 6x30; el archivo dice que debe ser la de 8x30')
else:
    print('   ya estaba correcta')
env.flush_all(); env.cr.commit()
print('')
for l in bom.bom_line_ids.sorted(lambda x: x.product_id.default_code or ''):
    print('      %-10s %s' % (l.product_id.default_code, (l.product_id.name or '')[:44]))
