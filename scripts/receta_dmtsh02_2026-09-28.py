# -*- coding: utf-8 -*-
"""DMTSH02 consumia la hoja CUALITATIVA. Le toca la semicuantitativa.

DMTSH02 "Prueba rapida de TSH semicuantitativa" tenia en su receta SPHMC37,
que es la hoja maestra CUALITATIVA, mientras su cartucho ya era el MPCAR52,
el semicuantitativo. Estaba mezclando las dos versiones de la prueba.

Confirmado por Mery el 28-sep-2026. Los numeros ya cruzaban en el resto del
catalogo: 37 = cualitativa, 52 = semicuantitativa, en hoja y en cartucho.

Idempotente.
"""
mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

pt = env['product.product'].search([('default_code', '=', 'DMTSH02')], limit=1)
h37 = env['product.product'].search([('default_code', '=', 'SPHMC37')], limit=1)
h52 = env['product.product'].search([('default_code', '=', 'SPHMC52')], limit=1)
assert pt and h37 and h52, 'Falta DMTSH02 / SPHMC37 / SPHMC52'

lineas = env['mrp.bom.line'].search([
    ('bom_id.product_tmpl_id', '=', pt.product_tmpl_id.id), ('product_id', '=', h37.id)])
for l in lineas:
    l.write({'product_id': h52.id})
env.cr.commit()

print('cambiadas: %d' % len(lineas))
for c in env['mrp.bom.line'].search([('bom_id.product_tmpl_id', '=', pt.product_tmpl_id.id)]):
    print('  %s x %s' % (c.product_id.default_code, c.product_qty))
