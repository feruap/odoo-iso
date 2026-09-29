# -*- coding: utf-8 -*-
"""Dos correcciones de Calidad, por la ORM en vez de SQL a pelo.

Diana las dejo listas en staging y preparo los .sql para produccion. Se
rehacen con la ORM porque el SQL se salta las validaciones y, en el caso de
la copia, enumeraba mas de 30 columnas a mano: el dia que alguien agregue un
campo a esa tabla, la copia lo perderia en silencio. copy() se lleva el
registro completo.

A) MAVI-15 duplicado en DMFRT02, DMPSA01 y DMTSH02
   Cada uno tiene 4 lineas donde van 2 (control negativo seq 10 + control
   positivo seq 20). Se borran las 6 sobrantes. Verificado: ninguna esta
   usada por un analisis.

B) SPHMT03-05 (VPH, Pylorinet, TB-DxNet) sin configuracion
   Las variantes activas nacieron el 23-sep con CERO parametros, CERO
   especificaciones y CERO puntos de control: hoy esos tres productos NO SE
   PUEDEN ANALIZAR. Se copia la configuracion desde las plantillas
   archivadas, que si la tienen.

Idempotente. Con DRY_RUN=True no escribe nada: se corre asi primero para ver
que haria.
"""
DRY_RUN = False

SOBRANTES_MAVI15 = [89071, 89072, 89073, 89074, 89075, 89076]
# (plantilla archivada, plantilla activa, punto de calidad)
COPIAS = [(1507, 2377, 308), (1508, 2378, 309), (1509, 2379, 310)]

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

REL = env['amunet.quality.parameter.product.rel']
CFG = env['amunet.quality.parameter.specification.config']
DET = env['amunet.quality.test.line.detail']

print('=' * 72)
print('A) MAVI-15 duplicado')
sobrantes = CFG.browse(SOBRANTES_MAVI15).exists()
assert len(sobrantes) == len(SOBRANTES_MAVI15), 'Faltan registros: esperados %d, hay %d' % (
    len(SOBRANTES_MAVI15), len(sobrantes))
for c in sobrantes:
    usos = DET.search_count([('specification_config_id', '=', c.id)])
    clave = c.product_parameter_rel_id.product_tmpl_id.default_code
    codigo = c.product_parameter_rel_id.parameter_id.code
    assert codigo == 'MAVI-15', '%s no es MAVI-15, es %s' % (c.id, codigo)
    assert usos == 0, 'El %s (%s) tiene %d usos: NO se borra' % (c.id, clave, usos)
    print('  borrar %s  %-9s %-18s seq %s  usos %s' % (
        c.id, clave, c.specification_name, c.sequence, usos))
if not DRY_RUN:
    sobrantes.unlink()

print('-' * 72)
print('B) SPHMT03-05 sin configuracion')
for viejo, nuevo, punto_id in COPIAS:
    t_nuevo = env['product.template'].browse(nuevo)
    clave = t_nuevo.default_code or t_nuevo.name
    rels_viejos = REL.with_context(active_test=False).search([('product_tmpl_id', '=', viejo)])
    creados_rel, creados_cfg = 0, 0
    for rv in rels_viejos:
        rn = REL.search([('product_tmpl_id', '=', nuevo),
                         ('parameter_id', '=', rv.parameter_id.id)], limit=1)
        if not rn:
            creados_rel += 1
            if not DRY_RUN:
                rn = rv.copy({'product_tmpl_id': nuevo})
        existentes = CFG.search([('product_parameter_rel_id', '=', rn.id)]) if rn else CFG
        faltan = rv.specification_config_ids.filtered(
            lambda c: c.specification_name not in existentes.mapped('specification_name'))
        creados_cfg += len(faltan)
        if not DRY_RUN:
            for c in faltan:
                c.copy({'product_parameter_rel_id': rn.id, 'product_tmpl_id': nuevo})
    punto = env['amunet.quality.point'].browse(punto_id)
    variante = t_nuevo.product_variant_ids[:1]
    ya_en_punto = variante and variante in punto.product_ids
    if not ya_en_punto and not DRY_RUN and variante:
        punto.write({'product_ids': [(4, variante.id)]})
    print('  %-9s tmpl %s: %d parametros + %d especificaciones%s' % (
        clave, nuevo, creados_rel, creados_cfg,
        '' if ya_en_punto else '  + punto de control %s' % punto_id))

if not DRY_RUN:
    env.cr.commit()

print('-' * 72)
print('ESTADO FINAL' if not DRY_RUN else 'SIMULACION (no se escribio nada)')
for code in ('DMFRT02', 'DMPSA01', 'DMTSH02'):
    n = CFG.search_count([('product_parameter_rel_id.product_tmpl_id.default_code', '=', code),
                          ('product_parameter_rel_id.parameter_id.code', '=', 'MAVI-15')])
    print('  %-9s MAVI-15: %d lineas' % (code, n))
for viejo, nuevo, punto in COPIAS:
    t = env['product.template'].browse(nuevo)
    print('  %-9s parametros=%d especificaciones=%d' % (
        t.default_code, REL.search_count([('product_tmpl_id', '=', nuevo)]),
        CFG.search_count([('product_parameter_rel_id.product_tmpl_id', '=', nuevo)])))
print('=' * 72)
