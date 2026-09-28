"""
GOTEROS -- desactivar VAMA-038 (produccion)
===========================================
Los 7 goteros (STGOT01-07) tienen VAMA-038, y MAVI-17 "Conteo de gotas" (5-10)
ya cubre esa evaluacion. Se desactiva el parametro y sus configuraciones en los
goteros, para que los analisis por venir no lo pidan.

AJUSTE sobre la version original, 28-sep-2026: se busca por CODIGO DE PARAMETRO
y clave de producto, no por ids escritos a mano. Los ids 408-414 hoy si
corresponden a los goteros (verificado), pero un id fijo desactiva a ciegas lo
que haya en esa fila: VAMA-038 existe en 50 productos mas, y si el script se
corre en otra base o despues de una migracion apaga parametros de calidad de
quien no debe.

Los analisis YA HECHOS no se tocan: sus lineas son copias propias y se quedan
como estan. Esto solo cambia lo que heredan los nuevos.

Solicitado por: Diana Flores -- Control de Calidad, 2026-09-25
Idempotente: si ya estan desactivados, no hace nada.
"""

Rel = env['amunet.quality.parameter.product.rel']
Cfg = env['amunet.quality.parameter.specification.config']

CODIGO = 'VAMA-038'
GOTEROS = ['STGOT0%d' % n for n in range(1, 8)]

rels = Rel.search([
    ('parameter_code', '=', CODIGO),
    ('product_tmpl_id.default_code', 'in', GOTEROS),
])
print('-- %s en goteros: %s relacion(es) encontradas --' % (CODIGO, len(rels)))
if not rels:
    print('   nada que desactivar')
for rel in rels:
    clave = rel.product_tmpl_id.default_code
    cfgs = Cfg.with_context(active_test=False).search([
        ('product_parameter_rel_id', '=', rel.id)])
    activas = cfgs.filtered(lambda c: c.active)
    if not rel.active and not activas:
        print('   %-9s rel %-5s ya estaba desactivado' % (clave, rel.id))
        continue
    print('   %-9s rel %-5s %s config(s) activa(s) -> desactivando' % (
        clave, rel.id, len(activas)))
    if activas:
        activas.write({'active': False})
    if rel.active:
        rel.write({'active': False})

env.cr.commit()

print('\n-- Verificacion: parametros que quedan activos en cada gotero --')
for clave in GOTEROS:
    act = Rel.search([('product_tmpl_id.default_code', '=', clave), ('active', '=', True)])
    if not act:
        print('   %-9s sin parametros activos (revisar: no deberia quedar vacio)' % clave)
        continue
    codigos = sorted(act.mapped('parameter_code'))
    queda = CODIGO in codigos
    print('   %-9s %s%s' % (clave, codigos, '   <-- OJO, sigue activo' if queda else ''))

print('\n-- Que NO se toco (mismo parametro en otros productos) --')
otros = Rel.search([('parameter_code', '=', CODIGO), ('active', '=', True),
                    ('product_tmpl_id.default_code', 'not in', GOTEROS)])
print('   %s producto(s) conservan %s activo: %s' % (
    len(otros), CODIGO, ', '.join(sorted(otros.mapped('product_tmpl_id.default_code'))) or '-'))
