"""Limpia los renglones sobrantes de los dos analisis EN PROCESO de hojas CM.

Autorizado por Mery el 29-sep-2026, con dos permisos explicitos: "el 503 se puede
borrar" (lo platico con Diana) y "regresalos tu y borra".

POR QUE HACE FALTA ESTE PASO APARTE: el modulo de Calidad prohibe borrar renglones de
un analisis que no esta en borrador --
amunet_quality_test_line_detail.unlink() lo bloquea --, y QC/2026/00503 y 00504 estan
EN PROCESO. Es un candado de integridad del expediente, no un estorbo: el script SQL
de Calidad lo habria evadido sin enterarse.

El camino legitimo es regresar el analisis a BORRADOR, limpiar, y devolverlo a su
estado. Eso es lo que autorizo Mery y lo que hace este script, dejando en el historial
del analisis el paso completo y su razon -- el propio modelo exige razon de cambio
para escribir fuera de borrador, asi que el rastro queda por diseno.

QUE SE QUITA: los renglones que vienen de especificaciones ya desactivadas porque no
corresponden a una hoja maestra -- Letra, Sellado, Letra adecuada, Vial - Altura, y
los duplicados de Tiempo de liberacion, Tiempo de migracion y Deformidad o deterioro.

SIETE DE ELLOS TIENEN CAPTURA en cada analisis. Diana lo reviso con Mery y autorizo
descartarla: se capturo sobre renglones que no correspondian al producto.

RESULTADO: 8 renglones por analisis -- 3 MAVI-04 + 2 MAVI-07 + 2 MAVI-09 + 1 MAVI-11 --
igual que QC/2026/00505, que ya quedo asi por estar en borrador.

Idempotente.
"""
from markupsafe import Markup

Check = env['amunet.quality.check'].sudo()
Detail = env['amunet.quality.test.line.detail'].sudo()
RAZON = ('Limpieza de renglones que no corresponden a una hoja maestra, autorizada '
         'por Mery el 29-sep-2026 y revisada con Diana (Calidad).')

for qc in Check.browse([932, 933]).exists():
    sobran = Detail.search([('test_line_id.check_id', '=', qc.id)]).filtered(
        lambda d: d.specification_config_id and not d.specification_config_id.active)
    if not sobran:
        print('[ya] %s ya solo tiene los renglones que aplican' % qc.name); continue
    estado_original = qc.state
    nombres = sorted(set((d.specification_config_id.specification_name or '')
                         for d in sobran))
    print('%s (%s): %s renglones sobrantes -> %s' % (
        qc.name, estado_original, len(sobran), ', '.join(nombres)))

    # 1. a borrador, para que el candado permita limpiar
    qc.write({'state': 'draft', 'change_reason': RAZON + ' Paso 1 de 3: se regresa a '
              'borrador porque el sistema solo permite retirar renglones en ese estado.'})
    print('   [1/3] %s -> draft' % estado_original)

    # 2. limpiar
    n = len(sobran)
    sobran.unlink()
    print('   [2/3] %s renglones retirados' % n)

    # 3. de vuelta a su estado
    qc.write({'state': estado_original,
              'change_reason': RAZON + ' Paso 3 de 3: se devuelve a %s, su estado '
              'original.' % estado_original})
    qc.invalidate_recordset()
    print('   [3/3] draft -> %s  (quedo en %s)' % (estado_original, qc.state))

    qc.message_post(body=Markup(
        'Se retiraron <b>%s renglones</b> que no corresponden a una hoja maestra: '
        'Letra, Sellado, Letra adecuada, Vial - Altura y los duplicados de Tiempo de '
        'liberacion, Tiempo de migracion y Deformidad o deterioro. Venian de '
        'especificaciones copiadas de otro producto, ya desactivadas.<br/><br/>'
        '<b>Siete tenian captura</b>, y se descarto con autorizacion: Diana lo reviso '
        'con Mery el 29-sep-2026 y confirmo que se habia capturado sobre renglones que '
        'no correspondian al producto.<br/><br/>'
        'Para poder retirarlos hubo que regresar el analisis a <b>borrador</b> y '
        'devolverlo a <b>%s</b>: el sistema no permite quitar renglones de un analisis '
        'en proceso, y se respeto ese camino en vez de forzarlo por atras.<br/><br/>'
        'El analisis queda con los renglones que de verdad aplican: rasgaduras, '
        'manchas, deformidad, muestra positiva y negativa, tiempo de migracion y de '
        'liberacion, y altura.') % (n, estado_original))

print('\n=== los tres analisis de las hojas CM ===')
for qc in Check.browse([932, 933, 934]).exists():
    renglones = Detail.search([('test_line_id.check_id', '=', qc.id)])
    por_param = {}
    for d in renglones:
        p = d.specification_config_id.product_parameter_rel_id.parameter_code or '?'
        por_param[p] = por_param.get(p, 0) + 1
    print('   %s  %-9s %-12s %s renglones  ->  %s' % (
        qc.name, qc.product_id.default_code, qc.state, len(renglones),
        ', '.join('%s x%s' % (k, v) for k, v in sorted(por_param.items()))))
env.cr.commit()
