"""Los analisis de las hojas CM se quedan solo con los renglones que aplican.

Autorizado por Mery el 29-sep-2026, despues de platicarlo con Diana: "el 503 se
puede borrar". Cierra la PARTE 2 del fix_sphmc85_88_v2_seguro.sql que preparo
Calidad, hecho por la ORM.

DE DONDE VIENE: las cuatro hojas CM tenian especificaciones que no les corresponden
-- Letra, Sellado, Letra adecuada, Vial - Altura y un Tiempo de liberacion duplicado
--, copiadas de otro producto. Ya se desactivaron, pero los TRES ANALISIS en curso
seguian mostrando esos renglones y Calidad tenia que llenarlos:

    QC/2026/00503  SPHMC86   15 renglones (3 de ellos YA CAPTURADOS)
    QC/2026/00504  SPHMC87   15 renglones (vacios)
    QC/2026/00505  SPHMC88   15 renglones (vacios)

LO QUE SE BORRA, y esto es lo delicado: en el 00503 tres de esos renglones tenian
captura -- Letra, Sellado y Letra adecuada, justo los que NO aplican a una hoja
maestra. Diana lo reviso con Mery y autorizo descartarlos: se capturaron sobre
renglones que no correspondian al producto. Queda la justificacion escrita en el
propio analisis, como pide el control de cambios.

TAMBIEN se desactiva la segunda "Deformidad o deterioro" de cada hoja, la del
criterio VACIO. La decision es de Diana, en su aviso del 29-sep 17:14: "el filtro de
MAVI-04 ahora tambien elimina la entrada Deformidad o deterioro con criterio vacio
que quedaba duplicada en cada analisis". Se queda la que si tiene criterio.

RESULTADO ESPERADO, el que pidio Calidad: 8 renglones por analisis --
3 MAVI-04 + 2 MAVI-07 + 2 MAVI-09 + 1 MAVI-11.

Idempotente.
"""
from markupsafe import Markup

Cfg = env['amunet.quality.parameter.specification.config'].sudo()
Check = env['amunet.quality.check'].sudo()
Detail = env['amunet.quality.test.line.detail'].sudo()

DEFORMIDAD_VACIA = [86834, 86966, 87098, 87230]
ANALISIS = [932, 933, 934]

print('-- 1. la segunda "Deformidad o deterioro" (la del criterio vacio) --')
for cid in DEFORMIDAD_VACIA:
    c = Cfg.with_context(active_test=False).browse(cid)
    if not c.exists():
        print('   [ojo] %s no existe' % cid); continue
    prod = c.product_parameter_rel_id.product_tmpl_id.default_code
    if not c.active:
        print('   [ya] %-6s %s ya estaba desactivada' % (cid, prod)); continue
    assert not (c.acceptance_criteria or '').strip(), \
        'la %s tiene criterio, no es la sobrante: revisar' % cid
    c.write({'active': False})
    print('   [ok] %-6s %s desactivada (criterio vacio)' % (cid, prod))

print('\n-- 2. los renglones que ya no aplican, en los tres analisis --')
CAMPOS = ('result_binary_option', 'result_selection', 'result_ternary')
for qc in Check.browse(ANALISIS).exists():
    renglones = Detail.search([('test_line_id.check_id', '=', qc.id)])
    sobran = renglones.filtered(
        lambda d: d.specification_config_id and not d.specification_config_id.active)
    if not sobran:
        print('   [ya] %s ya solo tiene los renglones que aplican (%s)' % (
            qc.name, len(renglones))); continue
    con_datos = sobran.filtered(lambda d: any(
        (d[c] or '') for c in CAMPOS) or d.result_numeric is not None)
    print('   %s (%s): %s renglones, sobran %s (%s con captura)' % (
        qc.name, qc.product_id.default_code, len(renglones), len(sobran), len(con_datos)))
    for d in sobran:
        marca = 'CON CAPTURA' if d in con_datos else 'vacio'
        print('      quita %-26s %s' % (
            (d.specification_config_id.specification_name or '')[:26], marca))
    detalle = ', '.join(sorted(set(
        (d.specification_config_id.specification_name or '') for d in con_datos))) or 'ninguno'
    # El sistema PROHIBE borrar renglones de un analisis que no esta en borrador
    # (amunet_quality_test_line_detail.unlink). Es un candado de integridad del
    # expediente y se respeta: el script SQL de Calidad lo habria evadido.
    if qc.state != 'draft':
        print('      NO SE BORRA: %s esta en %s y el sistema solo permite borrar '
              'renglones en BORRADOR' % (qc.name, qc.state))
        print('      (las especificaciones ya estan desactivadas, asi que no '
              'apareceran en los analisis nuevos)')
        continue
    n_sobran, n_datos = len(sobran), len(con_datos)
    sobran.unlink()
    qc.message_post(body=Markup(
        'Se retiraron <b>%s renglones</b> que no corresponden a una hoja maestra: '
        'venian de especificaciones copiadas de otro producto (Letra, Sellado, Letra '
        'adecuada, Vial - Altura, y duplicados de Tiempo de liberacion/migracion y '
        'Deformidad o deterioro), ya desactivadas.<br/><br/>'
        '<b>%s tenian captura:</b> %s. Diana lo reviso con Mery el 29-sep-2026 y '
        'autorizo descartarla, porque se capturo sobre renglones que no correspondian '
        'al producto.<br/><br/>El analisis queda con los renglones que de verdad '
        'aplican: rasgaduras, manchas, deformidad, muestra positiva y negativa, '
        'tiempo de migracion y de liberacion, y altura.'
    ) % (n_sobran, n_datos, detalle))

print('\n=== como quedan ===')
for qc in Check.browse(ANALISIS).exists():
    renglones = Detail.search([('test_line_id.check_id', '=', qc.id)])
    por_param = {}
    for d in renglones:
        p = d.specification_config_id.product_parameter_rel_id.parameter_code or '?'
        por_param[p] = por_param.get(p, 0) + 1
    print('   %s  %-9s %s renglones  ->  %s' % (
        qc.name, qc.product_id.default_code, len(renglones),
        ', '.join('%s x%s' % (k, v) for k, v in sorted(por_param.items()))))
env.cr.commit()
