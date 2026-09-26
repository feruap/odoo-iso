# -*- coding: utf-8 -*-
"""Los seis ajustes que marco Mery en el archivo de soluciones (25-sep-2026).

Ella devolvio el mismo Excel que se le entrego, con los cambios dentro de las
celdas. Comparando celda por celda contra el original salieron estos seis:

    SPLPT01   pide analisis   si -> NO
    SPNPS01   caducidad       3 Meses -> 4 Meses
    SPSDC01   nombre          "(AD 0)" -> "(AD0)", para que quede como (AD1)
    SPSDC02   caducidad       1 Meses -> 3 Meses
    SPSHS03   caducidad       sin capturar -> 1 mes
    SPSPA05   caducidad       sin capturar -> 1 mes

Los dos ultimos son las dos que quedaron sin caducidad al darlas de alta. Y NO
llevan 6 meses como sus hermanas de serie, que era lo que yo suponia: llevan
1 mes. Menos mal que se pregunto.

El nombre se escribe tambien en es_MX: si solo se escribe el valor base, el
usuario sigue viendo el viejo.
"""
P = env['product.product'].sudo()
CAMBIOS = [
    ('SPLPT01', {'amunet_req_quality_control': False}),
    ('SPNPS01', {'amunet_expiration_text': '4 Meses'}),
    ('SPSDC01', {'name': 'Solución diluyente para conjugado (AD0)'}),
    ('SPSDC02', {'amunet_expiration_text': '3 Meses'}),
    ('SPSHS03', {'amunet_expiration_text': '1 mes'}),
    ('SPSPA05', {'amunet_expiration_text': '1 mes'}),
]
for cod, vals in CAMBIOS:
    p = P.search([('default_code','=',cod)], limit=1)
    assert p, 'no existe %s' % cod
    t = p.product_tmpl_id
    antes = {k: t[k] for k in vals}
    if all((antes[k] or '') == (v or '') if isinstance(v, str) else antes[k] == v
           for k, v in vals.items()):
        print('   %-10s ya estaba aplicado' % cod); continue
    t.write(vals)
    if 'name' in vals:
        # el nombre es traducible: hay que escribirlo tambien en es_MX
        t.with_context(lang='es_MX').write({'name': vals['name']})
    for k, v in vals.items():
        print('   %-10s %-28s %r -> %r' % (cod, k, antes[k], v))
env.flush_all(); env.cr.commit()
print('')
print('   === como quedan:')
for cod, _ in CAMBIOS:
    p = P.search([('default_code','=',cod)], limit=1)
    t = p.product_tmpl_id
    print('      %-10s caducidad=%-10s analisis=%-6s nombre=%s' % (
        cod, t.amunet_expiration_text or '-', t.amunet_req_quality_control,
        p.with_context(lang='es_MX').name[:46]))
