# -*- coding: utf-8 -*-
"""Caducidad y bandera de analisis de las 26 soluciones de captura.

Mery, 28-sep-2026: caducidad 3 dias, no piden analisis.

La grafia va como "3 Dias" para que quede igual que el conjugado ("15 Dias")
y no se abra una tercera forma de escribir lo mismo.
"""
mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

prods = env['product.product'].search([
    '|', '|',
    ('default_code', '=like', 'SPSCA%'),
    ('default_code', '=', 'SPSPC01'),
    ('default_code', '=', 'SPSAN01'),
])
assert len(prods) == 26, 'Se esperaban 26 y hay %d' % len(prods)

prods.product_tmpl_id.write({
    'amunet_expiration_text': '3 Dias',
    # Analisis de PRODUCCION apagado (es el que pidio Mery). El de RECEPCION
    # ya venia apagado: no se compran, se fabrican.
    'amunet_req_quality_control': False,
    'qc_required': False,
})
env.cr.commit()

for p in prods.sorted('default_code'):
    t = p.product_tmpl_id
    print('%-9s %-52s cad=%-8s analisis_prod=%s recep=%s' % (
        p.default_code, p.name[:52], t.amunet_expiration_text,
        t.amunet_req_quality_control, t.qc_required))
print('TOTAL %d' % len(prods))
