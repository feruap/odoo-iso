# -*- coding: utf-8 -*-
"""
Corrige evaluation_type en amunet_quality_test_line_detail para análisis
ABIERTOS de STBBM02, STREX01 y STREX02.

Las migraciones anteriores (41, 43) corrigieron el spec_config pero NO los
detalles ya generados en análisis en curso, que guardan su propia copia.

STBBM02: mavi_07_ternary → vama_multi_check (JSON ya correcto)
STREX01/02: mavi_07 → vama_multi_check + JSON correcto (fixed_sample_type)
"""
import json

JSON_NEG = {
    "fixed_sample_type": "negative",
    "positions": [{"index": 0, "type": "select",
        "label": "Patrón Observado (PRB-01)",
        "instruction": "Seleccione el patrón visualizado.",
        "options": [
            {"label": "#1 (Línea T muy intensa)",      "value": "result_1"},
            {"label": "#2 (Línea T intensa)",           "value": "result_2"},
            {"label": "#3 (Línea T moderada)",          "value": "result_3"},
            {"label": "#4 (Línea T tenue)",             "value": "result_4"},
            {"label": "#5 (Sin línea T, solo línea C)", "value": "result_5"},
            {"label": "N/A (control no disponible)",    "value": "na"},
        ]}],
    "phrase_template": "Muestra negativa: Patrón {0}",
    "evaluation": {"rules": [
        {"sample_type": "negative", "result": "result_5", "verdict": "pass",
         "message": "Muestra Negativa: Patrón #5 (sin línea T) - CUMPLE"},
        {"sample_type": "negative", "result": "result_1", "verdict": "fail",
         "message": "Muestra Negativa: Patrón #1 (línea T visible) - NO CUMPLE"},
        {"sample_type": "negative", "result": "result_2", "verdict": "fail",
         "message": "Muestra Negativa: Patrón #2 (línea T visible) - NO CUMPLE"},
        {"sample_type": "negative", "result": "result_3", "verdict": "fail",
         "message": "Muestra Negativa: Patrón #3 (línea T visible) - NO CUMPLE"},
        {"sample_type": "negative", "result": "result_4", "verdict": "fail",
         "message": "Muestra Negativa: Patrón #4 (línea T visible) - NO CUMPLE"},
        {"sample_type": "negative", "result": "na", "verdict": "not_applicable",
         "message": "Muestra Negativa: Control no disponible - N/A"},
    ]},
}

JSON_POS = {
    "fixed_sample_type": "positive",
    "positions": [{"index": 0, "type": "select",
        "label": "Patrón Observado (PRB-01)",
        "instruction": "Seleccione el patrón visualizado.",
        "options": [
            {"label": "#1 (Línea T muy intensa)",      "value": "result_1"},
            {"label": "#2 (Línea T intensa)",           "value": "result_2"},
            {"label": "#3 (Línea T moderada)",          "value": "result_3"},
            {"label": "#4 (Línea T tenue)",             "value": "result_4"},
            {"label": "#5 (Sin línea T, solo línea C)", "value": "result_5"},
            {"label": "N/A (control no disponible)",    "value": "na"},
        ]}],
    "phrase_template": "Muestra positiva: Patrón {0}",
    "evaluation": {"rules": [
        {"sample_type": "positive", "result": "result_1", "verdict": "pass",
         "message": "Muestra Positiva: Patrón #1 - CUMPLE"},
        {"sample_type": "positive", "result": "result_2", "verdict": "pass",
         "message": "Muestra Positiva: Patrón #2 - CUMPLE"},
        {"sample_type": "positive", "result": "result_3", "verdict": "pass",
         "message": "Muestra Positiva: Patrón #3 - CUMPLE"},
        {"sample_type": "positive", "result": "result_4", "verdict": "pass",
         "message": "Muestra Positiva: Patrón #4 - CUMPLE"},
        {"sample_type": "positive", "result": "result_5", "verdict": "fail",
         "message": "Muestra Positiva: Patrón #5 (sin línea T) - NO CUMPLE"},
        {"sample_type": "positive", "result": "na", "verdict": "not_applicable",
         "message": "Muestra Positiva: Control no disponible - N/A"},
    ]},
}


def migrate(cr, version):
    import logging
    _logger = logging.getLogger(__name__)

    # 1. STBBM02: mavi_07_ternary → vama_multi_check (JSON ya correcto)
    cr.execute("""
        UPDATE amunet_quality_test_line_detail td
        SET evaluation_type = 'vama_multi_check', write_date = NOW()
        FROM amunet_quality_test_line tl
        JOIN amunet_quality_check qc ON qc.id = tl.check_id
        JOIN product_product pp ON pp.id = qc.product_id
        JOIN product_template pt ON pt.id = pp.product_tmpl_id
        JOIN amunet_quality_check_parameter p ON p.id = tl.parameter_id
        WHERE td.test_line_id = tl.id
          AND p.code = 'MAVI-07'
          AND td.evaluation_type = 'mavi_07_ternary'
          AND pt.default_code = 'STBBM02'
          AND qc.state NOT IN ('approved', 'rejected', 'done')
    """)
    _logger.info("STBBM02 detalles mavi_07_ternary → vama_multi_check: %d", cr.rowcount)

    # 2. STREX01/STREX02: mavi_07 → vama_multi_check + JSON correcto
    for code in ('STREX01', 'STREX02'):
        # Muestra negativa
        cr.execute("""
            UPDATE amunet_quality_test_line_detail td
            SET evaluation_type     = 'vama_multi_check',
                text_phrase_mapping = %s,
                write_date          = NOW()
            FROM amunet_quality_test_line tl
            JOIN amunet_quality_check qc ON qc.id = tl.check_id
            JOIN product_product pp ON pp.id = qc.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            JOIN amunet_quality_check_parameter p ON p.id = tl.parameter_id
            WHERE td.test_line_id = tl.id
              AND p.code = 'MAVI-07'
              AND td.evaluation_type = 'mavi_07'
              AND td.name = 'Muestra negativa'
              AND pt.default_code = %s
              AND qc.state NOT IN ('approved', 'rejected', 'done')
        """, (json.dumps(JSON_NEG, ensure_ascii=False), code))
        _logger.info("%s Muestra negativa mavi_07 → vama_multi_check: %d", code, cr.rowcount)

        # Muestra positiva (si existe con mavi_07)
        cr.execute("""
            UPDATE amunet_quality_test_line_detail td
            SET evaluation_type     = 'vama_multi_check',
                text_phrase_mapping = %s,
                write_date          = NOW()
            FROM amunet_quality_test_line tl
            JOIN amunet_quality_check qc ON qc.id = tl.check_id
            JOIN product_product pp ON pp.id = qc.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            JOIN amunet_quality_check_parameter p ON p.id = tl.parameter_id
            WHERE td.test_line_id = tl.id
              AND p.code = 'MAVI-07'
              AND td.evaluation_type = 'mavi_07'
              AND td.name = 'Muestra positiva'
              AND pt.default_code = %s
              AND qc.state NOT IN ('approved', 'rejected', 'done')
        """, (json.dumps(JSON_POS, ensure_ascii=False), code))
        _logger.info("%s Muestra positiva mavi_07 → vama_multi_check: %d", code, cr.rowcount)
