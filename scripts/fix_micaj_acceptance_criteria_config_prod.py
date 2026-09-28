"""
CORRECCION acceptance_criteria MICAJ (produccion)
=================================================
Ancho y Largo de la Caja Caple nacian con los criterios intercambiados:

    Ancho (rango 105-115)  decia "200 mm +/-5 mm"   <- del Largo
    Largo (rango 195-205)  decia "110 mm +/-5 mm"   <- del Ancho

El fix del 23-sep corrigio los analisis de entonces pero NO la configuracion
fuente, asi que cada analisis nuevo volvia a nacer mal. Esto arregla la fuente.

DOS AJUSTES sobre la version original, 28-sep-2026:

1. Por ORM, no por SQL. El acceptance_criteria de un analisis es un dato de
   negocio: un UPDATE directo se salta validaciones, computes, el historial y
   cualquier modulo que escuche el write. Regla del CLAUDE.md, y ya nos costo
   una vez (la forma de pago de SMP/26/00303).

2. Los analisis FIRMADOS O CERRADOS no se tocan. Regla de Mery: lo firmado es
   historia, los arreglos son para adelante. Se corrige la fuente -- que es lo
   que gobierna los analisis por venir -- y los analisis abiertos.

Solicitado por: Diana Flores -- Control de Calidad, 2026-09-28
Idempotente: solo escribe donde el criterio no es ya el correcto.
"""

Cfg = env['amunet.quality.parameter.specification.config']
Check = env['amunet.quality.check']
Detail = env['amunet.quality.test.line.detail']

# (nombre de la especificacion, min_value que la identifica, criterio correcto)
# El texto va con el signo mas-menos tal como lo escribe el sistema, para no
# introducir una variante nueva del mismo criterio.
CRITERIOS = [
    ('Ancho', 105, u'110 mm ±5 mm'),
    ('Largo', 195, u'200 mm ±5 mm'),
]

print('-- 1. Configuracion fuente (gobierna los analisis nuevos) --')
for nombre, minimo, correcto in CRITERIOS:
    cfgs = Cfg.search([
        ('specification_name', '=', nombre),
        ('min_value', '=', minimo),
        ('product_parameter_rel_id.product_tmpl_id.default_code', 'like', 'MICAJ%'),
    ])
    malas = cfgs.filtered(lambda c: (c.acceptance_criteria or '') != correcto)
    for c in malas:
        print('   %s %s: "%s" -> "%s"' % (
            c.product_parameter_rel_id.product_tmpl_id.default_code, nombre,
            c.acceptance_criteria or '(vacio)', correcto))
    if malas:
        malas.write({'acceptance_criteria': correcto})
    print('   %s: %s de %s configs corregidas' % (nombre, len(malas), len(cfgs)))

print('\n-- 2. Analisis ABIERTOS (los firmados quedan como estan) --')
for nombre, minimo, correcto in CRITERIOS:
    dets = Detail.search([
        ('name', '=', nombre),
        ('min_value', '=', minimo),
        ('check_id.product_id.default_code', 'like', 'MICAJ%'),
    ])
    abiertos = dets.filtered(
        lambda d: not d.check_id.user_authorized_id and d.check_id.state != 'done')
    firmados = dets - abiertos
    malas = abiertos.filtered(lambda d: (d.acceptance_criteria or '') != correcto)
    for d in malas:
        print('   %s (%s) %s: "%s" -> "%s"' % (
            d.check_id.name or d.check_id.id, d.check_id.product_id.default_code,
            nombre, d.acceptance_criteria or '(vacio)', correcto))
    if malas:
        malas.write({'acceptance_criteria': correcto})
    pend = firmados.filtered(lambda d: (d.acceptance_criteria or '') != correcto)
    print('   %s: %s corregidos en analisis abiertos; %s en analisis FIRMADOS que NO se tocan%s'
          % (nombre, len(malas), len(pend),
             (' (%s)' % ', '.join(sorted(set(
                 d.check_id.name or str(d.check_id.id) for d in pend)))) if pend else ''))

env.cr.commit()
print('\nListo. Todo analisis nuevo de MICAJ hereda ya los criterios correctos.')
