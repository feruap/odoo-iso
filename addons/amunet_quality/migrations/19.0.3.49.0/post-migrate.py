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

# param_id → (code, sequence, specs)
# specs = list of (spec_id, name, eval_type, extra_fields_dict)
PARAMS = [
    (145, 'MAVI-04', 10, [
        (689, 'Polvo',                  'binary_selection', {'acceptance_criteria': 'Sin polvo',                  'binary_option_pass': 'Sin polvo',                  'binary_option_fail': 'Con polvo',                 'binary_expected_option': 'without_prefix'}),
        (690, 'Manchas y/o suciedad',   'binary_selection', {'acceptance_criteria': 'Sin manchas y/o suciedad',   'binary_option_pass': 'Sin manchas y/o suciedad',   'binary_option_fail': 'Con manchas y/o suciedad',  'binary_expected_option': 'without_prefix'}),
        (691, 'Rasgaduras',             'binary_selection', {'acceptance_criteria': 'Sin rasgaduras',             'binary_option_pass': 'Sin rasgaduras',             'binary_option_fail': 'Con rasgaduras',            'binary_expected_option': 'without_prefix'}),
        (692, 'Deformidad o deterioro', 'binary_selection', {'acceptance_criteria': 'Sin deformidad o deterioro', 'binary_option_pass': 'Sin deformidad o deterioro', 'binary_option_fail': 'Con deformidad o deterioro','binary_expected_option': 'without_prefix'}),
        (693, 'Sellado',                'binary_selection', {'acceptance_criteria': 'Sellado adecuado',           'binary_option_pass': 'Sellado adecuado',           'binary_option_fail': 'Sellado deficiente',        'binary_expected_option': 'without_prefix'}),
    ]),
    (90, 'MGA-0486', 20, [
        (385, 'Hermeticidad', 'binary_selection', {
            'acceptance_criteria': 'Ausencia de colorante',
            'binary_prefix': 'Presencia/Ausencia', 'binary_suffix': 'de colorante',
            'binary_option_pass': 'Ausencia de colorante', 'binary_option_fail': 'Presencia de colorante',
            'binary_expected_option': 'without_prefix',
        }),
    ]),
    (151, 'MAVI-20', 25, [
        (706, 'Apariencia del reactivo liofilizado', 'binary_selection', {
            'acceptance_criteria': 'Blanco, compacto y sin humedad aparente',
            'binary_prefix': 'Apariencia', 'binary_suffix': 'del reactivo liofilizado',
            'binary_option_pass': 'Blanco, compacto y sin humedad aparente',
            'binary_option_fail': 'No cumple especificación',
            'binary_expected_option': 'without_prefix',
        }),
    ]),
    (69, 'MAVI-09', 30, [
        (71, 'Liberación de conjugado', 'numeric_range', {'acceptance_criteria': '1-30 segundos',   'min_value': 1,  'max_value': 30}),
        (72, 'Migración de conjugado',  'numeric_range', {'acceptance_criteria': '30-180 segundos', 'min_value': 30, 'max_value': 180}),
    ]),
    (65, 'MAVI-07', 40, [
        (628, 'Muestra negativa', 'vama_multi_check', {'acceptance_criteria': '#5',                 'sequence': 10}),
        (629, 'Muestra positiva', 'vama_multi_check', {'acceptance_criteria': '#1, #2, #3 y #4',   'sequence': 20}),
    ]),
    (149, 'INC-002', 50, [
        (709, 'Verificación de contenido de empaque', 'binary_selection', {
            'acceptance_criteria': 'Coincidencia con el contenido especificado en el manual vigente.',
            'binary_option_pass': 'Contenido coincide',
            'binary_option_fail': 'Contenido no coincide',
            'binary_expected_option': 'with_prefix',
        }),
    ]),
]


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
        for param_id, param_code, seq, specs in PARAMS:
            rel_id, created = _get_or_create_rel(cr, _logger, tmpl_id, param_id, param_code, seq)
            spec_count = 0
            for spec_id, spec_name, eval_type, extra_orig in specs:
                extra = dict(extra_orig)
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
