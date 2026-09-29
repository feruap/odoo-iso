# -*- coding: utf-8 -*-
"""Quitar la frase repetida en dos denominaciones genericas.

De donde salio: Mery reviso el certificado CER_005290926-02 (QC/2026/00514,
lote 0926/01/TUB) y noto que la denominacion generica decia dos veces "en
muestras de sangre total". Al barrer las 89 fichas del catalogo de pruebas
rapidas aparecio una segunda con el mismo vicio, la de Zika.

Este texto no vive en el producto: vive en amunet.prueba.rapida, y el
certificado lo encuentra emparejando su campo 'referencia' con la clave del
producto. Se corrige aqui, no en la ficha del producto.

Solo se quita la frase repetida; no se reescribe nada mas. Si el texto no es
exactamente el esperado, el script no lo toca y lo reporta: no se hacen
sustituciones a ciegas sobre un documento regulado.
"""
CAMBIOS = [
    ('DMATB01',
     'en muestras de sangre total en muestras de sangre total',
     'en muestras de sangre total'),
    ('DMZIK01',
     'del virus del zika del virus del zika',
     'del virus del zika'),
]

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)
PR = env['amunet.prueba.rapida']

hechos, sin_cambio = [], []
for referencia, viejo, nuevo in CAMBIOS:
    f = PR.search([('referencia', '=', referencia)])
    if len(f) != 1:
        sin_cambio.append((referencia, 'hay %d fichas con esa referencia' % len(f)))
        continue
    actual = f.descripcion or ''
    if viejo not in actual:
        sin_cambio.append((referencia, 'ya no dice la frase repetida'))
        continue
    f.descripcion = actual.replace(viejo, nuevo)
    hechos.append((referencia, f.id))

env.cr.commit()

print('=' * 84)
for ref, fid in hechos:
    f = PR.browse(fid)
    print('CORREGIDA  %-9s (ficha %s)' % (ref, fid))
    print('   %s' % (f.descripcion or '')[:150])
for ref, motivo in sin_cambio:
    print('SIN TOCAR  %-9s %s' % (ref, motivo))
print('-' * 84)
import re
for ref, _, _ in CAMBIOS:
    f = PR.search([('referencia', '=', ref)], limit=1)
    d = re.sub(r'<[^>]+>', '', (f.descripcion or '')).replace('&nbsp;', ' ')
    rep = re.search(r'(\b\w{3,}( \w{2,}){2,}\b).*\1', d)
    print('  %-9s frase repetida: %s' % (ref, rep.group(1) if rep else 'ninguna'))
print('=' * 84)
