"""Las cuatro hojas CM pierden las especificaciones que no les corresponden.

Autorizado por Mery el 29-sep-2026. Hace lo mismo que el script SQL que preparo
Calidad (fix_sphmc85_88_produccion.sql), PERO SIN CANCELAR NINGUN ANALISIS.

QUE PIDE EL SCRIPT DE CALIDAD, y esta bien: SPHMC85, 86, 87 y 88 tienen
especificaciones que se copiaron de otro producto al configurarlas y que una hoja
maestra no tiene:

    MAVI-04   Letra, Sellado, Letra adecuada     (son de caja / vial)
    MAVI-09   Tiempo de liberacion duplicado
    MAVI-11   Vial - Altura                      (una hoja no tiene vial)

POR QUE NO SE SIGUE SU SCRIPT AL PIE DE LA LETRA: su paso 1 cancela por UPDATE
directo los analisis 932, 933 y 934 -- QC/2026/00503, 00504 y 00505, los de las
hojas del combo mosquito que entraron el 17-sep --, dos de ellos EN PROCESO y con 15
renglones cada uno. Su paso 2 borra los renglones capturados. Tres problemas:

  1. Un UPDATE directo evade el control de cambios del modelo: amunet.quality.check
     exige razon de cambio fuera de borrador, y asi no queda rastro.
  2. Se pierde lo capturado, y las cuatro hojas se quedan sin analisis: 3,600 cm
     detenidos en cuarentena. Justo ayer se pidio el analisis de la hoja de Dengue
     para que las cuatro salieran juntas.
  3. NO HACE FALTA. Desactivar la especificacion basta: deja de aparecer en los
     analisis nuevos y los que ya existen conservan sus renglones. Comprobado hoy
     mismo con las 12 especificaciones duplicadas que usaban analisis abiertos.

QUE HACE ESTE SCRIPT:
  - Desactiva las 23 especificaciones ajenas (una de las 24 del script original,
    la 86862, ya se borro hoy en la limpieza de duplicados).
  - Corrige el tipo de evaluacion de MAVI-11 en SPHMC85, que es el paso 4 del
    script de Calidad y esa si es una correccion limpia.
  - NO toca los analisis.

Idempotente.
"""

Cfg = env['amunet.quality.parameter.specification.config'].sudo()
Check = env['amunet.quality.check'].sudo()

AJENAS = [86832, 86833, 86835, 86861, 86862, 86943,
          86964, 86965, 86967, 86993, 86994, 87075,
          87096, 87097, 87099, 87125, 87126, 87207,
          87228, 87229, 87231, 87257, 87258, 87339]
ANALISIS = [932, 933, 934]

print('-- estado de los analisis ANTES (no se deben tocar) --')
antes = {}
for qc in Check.browse(ANALISIS).exists():
    n = sum(len(tl.detail_line_ids) for tl in qc.test_line_ids) if qc.test_line_ids else 0
    antes[qc.id] = (qc.state, n)
    print('   %s  %-9s %-12s %s renglones' % (
        qc.name, qc.product_id.default_code, qc.state, n))

print('\n-- desactivando las especificaciones ajenas --')
hechas, ya, faltan = 0, 0, []
for cid in AJENAS:
    c = Cfg.with_context(active_test=False).browse(cid)
    if not c.exists():
        faltan.append(cid); continue
    prod = c.product_parameter_rel_id.product_tmpl_id.default_code
    param = c.product_parameter_rel_id.parameter_code
    if not c.active:
        ya += 1
        print('   [ya] %-6s %-9s %-10s %s' % (cid, prod, param, c.specification_name))
        continue
    c.write({'active': False})
    hechas += 1
    print('   [ok] %-6s %-9s %-10s %s' % (cid, prod, param, c.specification_name))
if faltan:
    print('   (ya no existian: %s -- la 86862 se borro hoy en la limpieza de duplicados)' % faltan)

print('\n-- el tipo de evaluacion de MAVI-11 en SPHMC85 --')
c = Cfg.browse(86896)
if not c.exists():
    print('   [ojo] no existe la especificacion 86896')
elif c.evaluation_type == 'conditional_numeric_range':
    print('   [ya] ya es conditional_numeric_range')
else:
    antes_tipo = c.evaluation_type
    c.write({'evaluation_type': 'conditional_numeric_range'})
    print('   [ok] %s -> conditional_numeric_range  (%s)' % (antes_tipo, c.specification_name))

print('\n-- estado de los analisis DESPUES --')
for qc in Check.browse(ANALISIS).exists():
    n = sum(len(tl.detail_line_ids) for tl in qc.test_line_ids) if qc.test_line_ids else 0
    st, n0 = antes.get(qc.id, ('?', 0))
    igual = 'INTACTO' if (qc.state == st and n == n0) else 'CAMBIO!'
    print('   %s  %-12s %s renglones   %s' % (qc.name, qc.state, n, igual))

print('\n-- que le queda a cada hoja --')
for clave in ('SPHMC85', 'SPHMC86', 'SPHMC87', 'SPHMC88'):
    activas = Cfg.search([
        ('product_parameter_rel_id.product_tmpl_id.default_code', '=', clave),
        ('active', '=', True)])
    print('   %s: %s especificaciones -> %s' % (
        clave, len(activas),
        ', '.join(sorted(set('%s/%s' % (a.product_parameter_rel_id.parameter_code,
                                        a.specification_name) for a in activas))[:9])))
print('\n   desactivadas: %s   ya lo estaban: %s' % (hechas, ya))
env.cr.commit()
