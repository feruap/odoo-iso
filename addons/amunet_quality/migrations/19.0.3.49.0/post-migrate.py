# -*- coding: utf-8 -*-
"""
Migración 49.0 — Parámetros estándar para 11 productos PCR rápida.

Los productos DL (PCR rápida) llevan los mismos parámetros que los DM
cualitativos, más MAVI-20 (reactivo liofilizado) como extra.

Parámetros a configurar (en este orden):
  1. MAVI-04  (ID 145) Aspectos Visuales del empaque
  2. MGA-0486 (ID  90) Hermeticidad
  3. MAVI-20  (ID 151) Aspectos de reactivos liofilizados  ← nuevo para PCR
  4. MAVI-09  (ID  69) Desempeño del tiempo de flujo capilar
  5. MAVI-07  (ID  65) Visualización de líneas resultado base
  6. INC-002  (ID 149) Verificación de contenido de empaque

Para DLVPH01, que ya tiene MAVI-04 / MAVI-07 / MAVI-09, solo se agregan
los tres faltantes: MGA-0486, MAVI-20, INC-002.

Referencia: CERPT-000 VPH-NET; ESPPT-061; TAPT-061; PNOCC-002
"""

PRODUCTOS_PCR = (
    'DLVPH01', 'DLSAN01', 'DLISL01', 'DLECO01', 'DLTB02',
    'DLKRS01', 'DLAUR01', 'DLCAM01', 'DLCGO01', 'DLENT01', 'DLVIH01',
)

# (codigo, nombre_esperado_del_parametro, secuencia, specs)
# specs = (nombre_en_la_base, nombre_para_la_config, tipo, extras)
#
# NO se usan IDs fijos: se resuelven por codigo/nombre en cada base.
# Los IDs no son iguales entre staging y produccion -- se asignan segun el
# orden en que se creo cada registro. Esta migracion fallo el 08-sep-2026 al
# validarla sobre un clon de produccion: MAVI-20 es 151 en staging y 150 en
# produccion, y aborto con ForeignKeyViolation.
#
# Peor todavia: el spec 706 apunta en produccion a 'Capacidad de cierre', que
# es otra cosa. De haber pasado la llave foranea, habria colgado el reactivo
# liofilizado de una especificacion equivocada SIN FALLAR, en registros de
# calidad. Por eso ahora todo se busca por nombre.
PARAMS = [
    ('MAVI-04', 'Aspectos Visuales', 10, [
        ('Polvo', 'Polvo',                  'binary_selection', {'acceptance_criteria': 'Sin polvo',                  'binary_option_pass': 'Sin polvo',                  'binary_option_fail': 'Con polvo',                 'binary_expected_option': 'without_prefix'}),
        ('Manchas y/o suciedad', 'Manchas y/o suciedad',   'binary_selection', {'acceptance_criteria': 'Sin manchas y/o suciedad',   'binary_option_pass': 'Sin manchas y/o suciedad',   'binary_option_fail': 'Con manchas y/o suciedad',  'binary_expected_option': 'without_prefix'}),
        ('Rasgaduras', 'Rasgaduras',             'binary_selection', {'acceptance_criteria': 'Sin rasgaduras',             'binary_option_pass': 'Sin rasgaduras',             'binary_option_fail': 'Con rasgaduras',            'binary_expected_option': 'without_prefix'}),
        ('Deformidad o deterioro', 'Deformidad o deterioro', 'binary_selection', {'acceptance_criteria': 'Sin deformidad o deterioro', 'binary_option_pass': 'Sin deformidad o deterioro', 'binary_option_fail': 'Con deformidad o deterioro','binary_expected_option': 'without_prefix'}),
        ('Sellado', 'Sellado',                'binary_selection', {'acceptance_criteria': 'Sellado adecuado',           'binary_option_pass': 'Sellado adecuado',           'binary_option_fail': 'Sellado deficiente',        'binary_expected_option': 'without_prefix'}),
    ]),
    ('MGA-0486', None, 20, [
        ('Hermeticidad', 'Hermeticidad', 'binary_selection', {
            'acceptance_criteria': 'Ausencia de colorante',
            'binary_prefix': 'Presencia/Ausencia', 'binary_suffix': 'de colorante',
            'binary_option_pass': 'Ausencia de colorante', 'binary_option_fail': 'Presencia de colorante',
            'binary_expected_option': 'without_prefix',
        }),
    ]),
    ('MAVI-20', None, 25, [
        ('Aspectos del liofilizado', 'Apariencia del reactivo liofilizado', 'binary_selection', {
            'acceptance_criteria': 'Blanco, compacto y sin humedad aparente',
            'binary_prefix': 'Apariencia', 'binary_suffix': 'del reactivo liofilizado',
            'binary_option_pass': 'Blanco, compacto y sin humedad aparente',
            'binary_option_fail': 'No cumple especificación',
            'binary_expected_option': 'without_prefix',
        }),
    ]),
    ('MAVI-09', None, 30, [
        ('Liberación de conjugado', 'Liberación de conjugado', 'numeric_range', {'acceptance_criteria': '1-30 segundos',   'min_value': 1,  'max_value': 30}),
        ('Migración de conjugado', 'Migración de conjugado',  'numeric_range', {'acceptance_criteria': '30-180 segundos', 'min_value': 30, 'max_value': 180}),
    ]),
    ('MAVI-07', None, 40, [
        ('Muestra negativa', 'Muestra negativa', 'vama_multi_check', {'acceptance_criteria': '#5',                 'sequence': 10}),
        ('Muestra positiva', 'Muestra positiva', 'vama_multi_check', {'acceptance_criteria': '#1, #2, #3 y #4',   'sequence': 20}),
    ]),
    ('INC-002', None, 50, [
        ('Verificación de contenido de empaque', 'Verificación de contenido de empaque', 'binary_selection', {
            'acceptance_criteria': 'Coincidencia con el contenido especificado en el manual vigente.',
            'binary_option_pass': 'Contenido coincide',
            'binary_option_fail': 'Contenido no coincide',
            'binary_expected_option': 'with_prefix',
        }),
    ]),
]


def _resolver_parametro(cr, logger, code, nombre_esperado):
    """Devuelve el id del parametro EN ESTA BASE, buscandolo por su codigo.

    Ojo con MAVI-04: hay cuatro parametros con ese mismo codigo y distinto
    nombre ('Aspectos', 'Aspectos Visuales', 'Aspectos Apariencia del
    empaque', 'Aspectos Estructura del hisopo'). Por eso se acepta un nombre
    esperado para desempatar.
    """
    if nombre_esperado:
        cr.execute("""
            SELECT id FROM amunet_quality_check_parameter
            WHERE code = %s AND name = %s
        """, (code, nombre_esperado))
        filas = cr.fetchall()
        if len(filas) == 1:
            return filas[0][0]

    cr.execute("SELECT id, name FROM amunet_quality_check_parameter WHERE code = %s", (code,))
    filas = cr.fetchall()
    if not filas:
        raise Exception(
            "Migracion 49.0: no existe el parametro con codigo %s en esta base. "
            "Hay que darlo de alta antes de correr la migracion." % code)
    if len(filas) > 1:
        raise Exception(
            "Migracion 49.0: el codigo %s corresponde a %d parametros distintos (%s). "
            "Se necesita un nombre esperado para desempatar." %
            (code, len(filas), ', '.join('%s=%s' % (f[0], f[1]) for f in filas)))
    return filas[0][0]


def _resolver_spec(cr, logger, param_id, nombre_en_bd, eval_type, extra):
    """Devuelve el id de la especificacion bajo ese parametro. La crea si falta.

    En produccion 'Verificacion de contenido de empaque' (INC-002) no existia,
    asi que no basta con buscarla: hay que poder crearla.
    """
    cr.execute("""
        SELECT id FROM amunet_quality_check_parameter_specification
        WHERE parameter_id = %s AND name = %s
    """, (param_id, nombre_en_bd))
    fila = cr.fetchone()
    if fila:
        return fila[0]

    cr.execute("""
        SELECT COALESCE(MAX(sequence), 0) + 10
        FROM amunet_quality_check_parameter_specification WHERE parameter_id = %s
    """, (param_id,))
    seq = cr.fetchone()[0] or 10

    cr.execute("""
        INSERT INTO amunet_quality_check_parameter_specification
            (parameter_id, name, display_name, evaluation_type, acceptance_criteria,
             sequence, active, create_date, write_date, create_uid, write_uid)
        VALUES (%s, %s, %s, %s, %s, %s, true, NOW(), NOW(), 1, 1)
        RETURNING id
    """, (param_id, nombre_en_bd, nombre_en_bd, eval_type,
          extra.get('acceptance_criteria'), seq))
    nuevo = cr.fetchone()[0]
    logger.info("Migracion 49.0: creada la especificacion '%s' (id %s) bajo el parametro %s",
                nombre_en_bd, nuevo, param_id)
    return nuevo


def _get_or_create_rel(cr, logger, tmpl_id, param_id, param_code, seq):
    cr.execute("""
        SELECT id FROM amunet_quality_parameter_product_rel
        WHERE product_tmpl_id = %s AND parameter_id = %s
    """, (tmpl_id, param_id))
    row = cr.fetchone()
    if row:
        return row[0], False
    display = f'[{param_code}] {param_code}'
    cr.execute("""
        INSERT INTO amunet_quality_parameter_product_rel
            (product_tmpl_id, parameter_id, parameter_code, display_name,
             active, sequence, active_spec_count,
             create_date, write_date, create_uid, write_uid)
        VALUES (%s, %s, %s, %s, true, %s, 0, NOW(), NOW(), 1, 1)
        RETURNING id
    """, (tmpl_id, param_id, param_code, display, seq))
    rel_id = cr.fetchone()[0]
    logger.info("  Creada rel %s para tmpl_id=%d (rel_id=%d)", param_code, tmpl_id, rel_id)
    return rel_id, True


def _get_or_create_spec_config(cr, logger, rel_id, tmpl_id, param_id, spec_id,
                                spec_name, eval_type, extra):
    cr.execute("""
        SELECT id FROM amunet_quality_parameter_specification_config
        WHERE product_parameter_rel_id = %s AND specification_id = %s
    """, (rel_id, spec_id))
    if cr.fetchone():
        return False

    seq = extra.pop('sequence', 10)
    min_v = extra.pop('min_value', None)
    max_v = extra.pop('max_value', None)

    sets = ['product_parameter_rel_id', 'specification_id', 'specification_name',
            'evaluation_type', 'active', 'sequence', 'product_tmpl_id', 'parameter_id',
            'create_date', 'write_date', 'create_uid', 'write_uid']
    vals = [rel_id, spec_id, spec_name, eval_type, True, seq, tmpl_id, param_id,
            'NOW()', 'NOW()', 1, 1]

    for k, v in extra.items():
        sets.append(k)
        vals.append(v)
    if min_v is not None:
        sets.append('min_value')
        vals.append(min_v)
    if max_v is not None:
        sets.append('max_value')
        vals.append(max_v)

    placeholders = ', '.join(['NOW()' if v == 'NOW()' else '%s' for v in vals])
    real_vals = [v for v in vals if v != 'NOW()']
    cols = ', '.join(sets)

    cr.execute(
        f"INSERT INTO amunet_quality_parameter_specification_config ({cols}) VALUES ({placeholders})",
        real_vals
    )
    logger.info("    Spec '%s' (id=%d) agregada a rel_id=%d", spec_name, spec_id, rel_id)
    return True


def migrate(cr, version):
    import logging
    _logger = logging.getLogger(__name__)

    ph = ','.join(['%s'] * len(PRODUCTOS_PCR))
    cr.execute(
        f"SELECT id, default_code FROM product_template WHERE default_code IN ({ph})",
        PRODUCTOS_PCR
    )
    productos = {row[1]: row[0] for row in cr.fetchall()}
    _logger.info("Migración 49.0: %d productos PCR rápida encontrados", len(productos))

    for code, tmpl_id in sorted(productos.items()):
        _logger.info("Procesando %s (tmpl_id=%d)", code, tmpl_id)
        for param_code, nombre_esperado, seq, specs in PARAMS:
            param_id = _resolver_parametro(cr, _logger, param_code, nombre_esperado)
            rel_id, created = _get_or_create_rel(cr, _logger, tmpl_id, param_id, param_code, seq)
            spec_count = 0
            for nombre_en_bd, spec_name, eval_type, extra_orig in specs:
                extra = dict(extra_orig)
                spec_id = _resolver_spec(cr, _logger, param_id, nombre_en_bd, eval_type, extra)
                added = _get_or_create_spec_config(
                    cr, _logger, rel_id, tmpl_id, param_id,
                    spec_id, spec_name, eval_type, extra
                )
                if added:
                    spec_count += 1

            if spec_count:
                cr.execute("""
                    UPDATE amunet_quality_parameter_product_rel
                    SET active_spec_count = (
                        SELECT COUNT(*) FROM amunet_quality_parameter_specification_config
                        WHERE product_parameter_rel_id = %s AND active = true
                    ), write_date = NOW()
                    WHERE id = %s
                """, (rel_id, rel_id))

    _logger.info("Migración 49.0 completa.")
