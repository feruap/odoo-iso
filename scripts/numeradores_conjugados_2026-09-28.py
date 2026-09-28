# -*- coding: utf-8 -*-
"""Numerador de lote propio para los 29 conjugados.

Los 29 colgaban de la secuencia generica "Serial Numbers" (id 15), sin
prefijo: sus lotes habrian salido como numero pelon, sin decir de que
producto son ni de que mes. El resto de los insumos usa la clave sin las dos
primeras letras -SPCDE01 -> CDE01- mas mes y anio.

Ninguno tiene lotes todavia, asi que no hay historico que respetar: es el
momento de hacerlo.

Escribir serial_prefix_format es lo que dispara la creacion de la secuencia
en amunet_lot; no se crea la ir.sequence a mano para no dejarla fuera del
mecanismo que la mantiene.

Idempotente.
"""
mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

conj = env['product.product'].search([('default_code', '=like', 'SPCDE%')])
assert conj, 'No hay conjugados'

con_lotes = env['stock.lot'].search_count([('product_id', 'in', conj.ids)])
assert not con_lotes, 'Hay %d lotes ya emitidos: revisar antes de tocar el numerador' % con_lotes

hechos, ya = [], []
for p in conj.sorted('default_code'):
    t = p.product_tmpl_id
    esperado = p.default_code[2:]
    if t.serial_prefix_format == esperado and t.lot_sequence_id and t.lot_sequence_id.prefix:
        ya.append(p.default_code)
        continue
    t.serial_prefix_format = esperado
    hechos.append((p.default_code, t.lot_sequence_id.prefix, t.lot_sequence_id.padding))

env.cr.commit()

print('=' * 70)
for clave, pref, pad in hechos:
    print('  %-9s -> %-22s padding %s' % (clave, pref, pad))
print('  ya estaban: %s' % (', '.join(ya) or 'ninguno'))
print('-' * 70)
malos = conj.filtered(lambda p: not p.product_tmpl_id.lot_sequence_id.prefix)
print('SIN PREFIJO todavia: %s' % (malos.mapped('default_code') or 'ninguno'))
print('=' * 70)
