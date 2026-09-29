# -*- coding: utf-8 -*-
"""STCPL04 en staging todavia genera lotes sin la C.

Karla lo reporto el 28-sep. En PRODUCCION ya se corrigio el prefijo
(CPL04...), pero en STAGING se quedo en PL04 y por eso el lote
PL04092601 nacio mal. Mientras el prefijo siga asi, cada recepcion de
prueba vuelve a generar el nombre equivocado.

Solo se toca staging. El lote mal nombrado de produccion (PL04092602) NO
se toca aqui: renombrar un lote de produccion se consulta antes.
"""
mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

p = env['product.product'].search([('default_code', '=', 'STCPL04')], limit=1)
assert p, 'No existe STCPL04'
t = p.product_tmpl_id
print('antes: %s' % (t.lot_sequence_id.prefix or '(sin prefijo)'))
t.serial_prefix_format = 'CPL04'
env.cr.commit()
print('ahora: %s' % t.lot_sequence_id.prefix)

malos = env['stock.lot'].search([('product_id', '=', p.id)]).filtered(
    lambda l: not l.name.startswith('CPL04'))
print('lotes que siguen mal nombrados en staging: %s' % (malos.mapped('name') or 'ninguno'))
