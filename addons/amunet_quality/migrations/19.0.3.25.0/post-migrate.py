import json
import logging

_logger = logging.getLogger(__name__)

# parameter_ids (mismos que SPHMC53/54)
PARAM_MAVI_04 = 1
PARAM_MAVI_07 = 65
PARAM_MAVI_09 = 69
PARAM_MAVI_11 = 64

# specification_ids base (heredados del catálogo de parámetros)
SPEC_ID_MANCHAS     = 171
SPEC_ID_RASGADURAS  = 170
SPEC_ID_DEFORMIDAD  = 204
SPEC_ID_LIBERACION  = 146
SPEC_ID_MIGRACION   = 126
SPEC_ID_ALTURA      = 414
SPEC_ID_POSITIVA    = 629
SPEC_ID_NEGATIVA    = 628

# Mapeo competitivo MAVI-07 (idéntico a SPHMC10-14, 53, 54)
OPTIONS = [
    {"label": "#1 (Línea T muy intensa)",              "value": "result_1"},
    {"label": "#2 (Línea T intensa)",                  "value": "result_2"},
    {"label": "#3 (Línea T moderada)",                 "value": "result_3"},
    {"label": "#4 (Línea T tenue)",                    "value": "result_4"},
    {"label": "#5 (Sin línea T, solo línea C)",        "value": "result_5"},
    {"label": "#6 (Sin línea C, con línea T visible)", "value": "result_6"},
    {"label": "#7 (Sin línea C ni línea T)",           "value": "result_7"},
    {"label": "N/A (control no disponible)",           "value": "na"},
]
POSITION = {
    "index": 0, "type": "select",
    "label": "Patrón Observado (PRB-01)",
    "instruction": "Seleccione el patrón visualizado.",
    "options": OPTIONS,
}
MAPPING_POSITIVE = json.dumps({
    "fixed_sample_type": "positive",
    "positions": [POSITION],
    "phrase_template": "Muestra positiva: Patrón {0}",
    "evaluation": {"rules": [
        {"sample_type": "positive", "result": "result_1", "verdict": "fail",           "message": "Muestra Positiva: Patrón #1 (línea T visible) - NO CUMPLE"},
        {"sample_type": "positive", "result": "result_2", "verdict": "fail",           "message": "Muestra Positiva: Patrón #2 (línea T visible) - NO CUMPLE"},
        {"sample_type": "positive", "result": "result_3", "verdict": "fail",           "message": "Muestra Positiva: Patrón #3 (línea T visible) - NO CUMPLE"},
        {"sample_type": "positive", "result": "result_4", "verdict": "fail",           "message": "Muestra Positiva: Patrón #4 (línea T visible) - NO CUMPLE"},
        {"sample_type": "positive", "result": "result_5", "verdict": "pass",           "message": "Muestra Positiva: Patrón #5 (sin línea T, solo C) - CUMPLE"},
        {"sample_type": "positive", "result": "result_6", "verdict": "fail",           "message": "Muestra Positiva: Patrón #6 (sin línea C) - NO CUMPLE"},
        {"sample_type": "positive", "result": "result_7", "verdict": "fail",           "message": "Muestra Positiva: Patrón #7 (sin línea C ni T) - NO CUMPLE"},
        {"sample_type": "positive", "result": "na",       "verdict": "not_applicable", "message": "Muestra Positiva: Control no disponible - N/A"},
    ]},
})
MAPPING_NEGATIVE = json.dumps({
    "fixed_sample_type": "negative",
    "positions": [POSITION],
    "phrase_template": "Muestra negativa: Patrón {0}",
    "evaluation": {"rules": [
        {"sample_type": "negative", "result": "result_1", "verdict": "pass",           "message": "Muestra Negativa: Patrón #1 (C+T, sin analito) - CUMPLE"},
        {"sample_type": "negative", "result": "result_2", "verdict": "pass",           "message": "Muestra Negativa: Patrón #2 (C+T, sin analito) - CUMPLE"},
        {"sample_type": "negative", "result": "result_3", "verdict": "pass",           "message": "Muestra Negativa: Patrón #3 (C+T, sin analito) - CUMPLE"},
        {"sample_type": "negative", "result": "result_4", "verdict": "pass",           "message": "Muestra Negativa: Patrón #4 (C+T, sin analito) - CUMPLE"},
        {"sample_type": "negative", "result": "result_5", "verdict": "fail",           "message": "Muestra Negativa: Patrón #5 (solo C, analito detectado) - NO CUMPLE"},
        {"sample_type": "negative", "result": "result_6", "verdict": "fail",           "message": "Muestra Negativa: Patrón #6 (sin línea C) - NO CUMPLE"},
        {"sample_type": "negative", "result": "result_7", "verdict": "fail",           "message": "Muestra Negativa: Patrón #7 (sin línea C ni T) - NO CUMPLE"},
        {"sample_type": "negative", "result": "na",       "verdict": "not_applicable", "message": "Muestra Negativa: Control no disponible - N/A"},
    ]},
})

PRODUCTS = {
    'SPHMC75': {
        'nombre': 'Antidoping Sangre 2 Parámetros (COC y AMP)',
        'descripcion': 'Prueba rápida para la detección de Antidoping 2 parámetros en sangre, combinación de drogas (Cocaína y Anfetamina)',
    },
    'SPHMC76': {
        'nombre': 'Antidoping Sangre 3 Parámetros (OPI, MET y THC)',
        'descripcion': 'Prueba rápida para la detección de Antidoping 3 parámetros en sangre, combinación de drogas (Opiáceos, Metanfetamina y Tetrahidrocannabinol)',
    },
}


def _create_rel(cr, product_code, param_id, param_code):
    """Crea o devuelve el rel de parámetro para el producto."""
    cr.execute("""
        SELECT r.id FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE pt.default_code = %s AND r.parameter_id = %s AND r.active = true
        LIMIT 1
    """, (product_code, param_id))
    row = cr.fetchone()
    if row:
        return row[0]
    cr.execute("""
        INSERT INTO amunet_quality_parameter_product_rel
          (product_tmpl_id, parameter_id, parameter_code, sequence, active,
           create_uid, write_uid, create_date, write_date)
        SELECT pt.id, %s, %s, 10, true, 1, 1, NOW(), NOW()
        FROM product_template pt WHERE pt.default_code = %s
        RETURNING id
    """, (param_id, param_code, product_code))
    return cr.fetchone()[0]


def _add_spec(cr, rel_id, spec_id, name, eval_type, seq=10,
              pass_opt='', fail_opt='', criteria='',
              min_val=0, max_val=0, mapping=None):
    """Inserta un spec_config si no existe ya (por nombre y rel)."""
    cr.execute("""
        SELECT 1 FROM amunet_quality_parameter_specification_config
        WHERE product_parameter_rel_id = %s AND specification_name = %s AND active = true
    """, (rel_id, name))
    if cr.fetchone():
        return 0
    cr.execute("""
        INSERT INTO amunet_quality_parameter_specification_config
          (product_parameter_rel_id, specification_id, specification_name,
           evaluation_type, sequence,
           binary_option_pass, binary_option_fail, acceptance_criteria,
           min_value, max_value, text_phrase_mapping,
           active, create_uid, write_uid, create_date, write_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s::jsonb, true, 1, 1, NOW(), NOW())
    """, (rel_id, spec_id, name, eval_type, seq,
          pass_opt, fail_opt, criteria, min_val, max_val,
          mapping))
    return 1


def migrate(cr, version):
    """Migración 3.25.0: configura SPHMC75 y SPHMC76 como competitivas.

    Agrega MAVI-04, MAVI-07 (competitivo), MAVI-09 y MAVI-11 con los
    mismos valores que SPHMC53/54 (antidoping saliva). Rangos MAVI-09:
    liberación 0-30 s, migración 30-180 s.
    """
    total = 0

    for code in ('SPHMC75', 'SPHMC76'):
        # MAVI-04
        rel04 = _create_rel(cr, code, PARAM_MAVI_04, 'MAVI-04')
        total += _add_spec(cr, rel04, SPEC_ID_MANCHAS,    'Manchas y/o suciedad',    'binary_selection', pass_opt='Sin Manchas y/o suciedad',    fail_opt='Con Manchas y/o suciedad',    criteria='Manchas y/o suciedad')
        total += _add_spec(cr, rel04, SPEC_ID_RASGADURAS, 'Rasgaduras',              'binary_selection', pass_opt='Sin Rasgaduras',              fail_opt='Con Rasgaduras',              criteria='Rasgaduras')
        total += _add_spec(cr, rel04, SPEC_ID_DEFORMIDAD, 'Deformidad o deterioro.', 'binary_selection', pass_opt='Sin Deformidad o deterioro.', fail_opt='Con Deformidad o deterioro.', criteria='Deformidad o deterioro.')

        # MAVI-07 competitivo
        rel07 = _create_rel(cr, code, PARAM_MAVI_07, 'MAVI-07')
        total += _add_spec(cr, rel07, SPEC_ID_POSITIVA, 'Muestra positiva', 'vama_multi_check', seq=1, mapping=MAPPING_POSITIVE)
        total += _add_spec(cr, rel07, SPEC_ID_NEGATIVA, 'Muestra negativa', 'vama_multi_check', seq=2, mapping=MAPPING_NEGATIVE)

        # MAVI-09 (liberación 0-30, migración 30-180)
        rel09 = _create_rel(cr, code, PARAM_MAVI_09, 'MAVI-09')
        total += _add_spec(cr, rel09, SPEC_ID_LIBERACION, 'Tiempo de liberación', 'numeric_range',
                           pass_opt='Captura [    ] segundos', fail_opt='No captura [    ] segundos',
                           criteria='Tiempo de liberación', min_val=0, max_val=30)
        total += _add_spec(cr, rel09, SPEC_ID_MIGRACION,  'Tiempo de migración',  'numeric_range',
                           pass_opt='Captura [    ] segundos', fail_opt='No captura [    ] segundos',
                           criteria='Tiempo de migración', min_val=30, max_val=180)

        # MAVI-11
        rel11 = _create_rel(cr, code, PARAM_MAVI_11, 'MAVI-11')
        total += _add_spec(cr, rel11, SPEC_ID_ALTURA, 'Altura 6 u 8 cm (según aplique)',
                           'conditional_numeric_range',
                           pass_opt='Seleccione', fail_opt='Opción A: 6 cm.',
                           criteria='Altura 6 u 8 cm (según aplique)')

        # Descripción
        info = PRODUCTS[code]
        desc_json = '{{"en_US": "<p>{0}</p>", "es_MX": "<p>{0}</p>"}}'.format(info['descripcion'])
        cr.execute("""
            UPDATE product_template
            SET description = %s::jsonb, write_date = NOW()
            WHERE default_code = %s
              AND (description IS NULL OR description::text IN ('null', '{}', '""'))
        """, (desc_json, code))

    _logger.info(
        "Migración 3.25.0 — SPHMC75/76 configuradas: %d specs insertados", total,
    )
