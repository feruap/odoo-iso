# -*- coding: utf-8 -*-
"""Marcar los 12 viales con la etapa "Llenado de Viales".

POR QUE VA PRIMERO. Todo el comportamiento nuevo de la linea cuelga de esta
bandera: el destino AMP/Entrada, la caducidad heredada del granel, el formato
de lote de la serie del producto, la exencion del candado de analisis y la
exencion del plan de empaque preguntan por 'amunet_etapa_ll == llenado'. Sin
ella el codigo esta en el servidor y no hace nada, y las correcciones de los
pasos y de la cuarentena -- que buscan por esta misma bandera -- no encuentran
ningun producto.

Se separo de las otras dos a proposito, para que se vea que es la llave que las
enciende y en que orden van:

    1. etapa_llenado_viales      <- esta
    2. pasos_llenado_viales      <- los 5 pasos de la ruta
    3. cuarentena_viales         <- los 5 dias + el punto de STBBM02

LOS 12. Son los que Mery y Fer cerraron el 24-sep: los 11 de la lista original
mas STBTR02 y STBHB01, que son los de MAYOR existencia del grupo y no estaban
en ninguna lista previa. STHEB01 quedo fuera: se elimino, el bueno es STBHE01.

Idempotente.
"""
CLAVES = [
    'STACM01', 'STBAC01', 'STBBM01', 'STBBM02', 'STBCH01', 'STBDN01',
    'STBHB01', 'STBHE01', 'STBTR01', 'STBTR02', 'STRDI01', 'STSAL01',
]
ETAPA = 'llenado'

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

puestos, ya_estaban, no_existen, con_otra = [], [], [], []
for clave in CLAVES:
    p = env['product.product'].search([('default_code', '=', clave)], limit=1)
    if not p:
        no_existen.append(clave)
        continue
    tmpl = p.product_tmpl_id
    if tmpl.amunet_etapa_ll == ETAPA:
        ya_estaban.append(clave)
        continue
    if tmpl.amunet_etapa_ll:
        # No se pisa una etapa distinta sin avisar: seria reclasificar un
        # producto a espaldas de quien lo puso.
        con_otra.append((clave, tmpl.amunet_etapa_ll))
        continue
    tmpl.amunet_etapa_ll = ETAPA
    puestos.append(clave)

env.cr.commit()

print('=' * 78)
print('ETAPA "Llenado de Viales" PUESTA EN %d: %s' % (len(puestos), ', '.join(puestos)))
print('YA LA TENIAN (%d): %s' % (len(ya_estaban), ', '.join(ya_estaban) or '-'))
print('NO EXISTEN (%d): %s' % (len(no_existen), ', '.join(no_existen) or '-'))
if con_otra:
    print('!! CON OTRA ETAPA, NO SE TOCARON: %s' % ', '.join(
        '%s=%s' % (c, e) for c, e in con_otra))
print('-' * 78)
total = env['product.template'].search_count([('amunet_etapa_ll', '=', ETAPA)])
print('TOTAL de productos en la etapa llenado: %d' % total)
print('=' * 78)
