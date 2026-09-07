# -*- coding: utf-8 -*-
"""
Corrige evaluation_type mavi_07_ternary → vama_multi_check en buffers STBBM02 y STBHE01.

STBBM02: el JSON ya es correcto; solo cambia el tipo.
STBHE01: cambia el tipo y agrega el JSON estándar de buffer (idéntico a STBPR03).
"""
import json

# JSON estándar para buffer cualitativo — igual que STBPR03
JSON_NEGATIVA = {
    "fixed_sample_type": "negative",
    "positions": [{
        "index": 0, "type": "select",
        "label": "Patrón Observado (PRB-01)",
        "instruction": "Seleccione el patrón visualizado.",
        "options": [
            {"label": "#1 (Línea T muy intensa)",  "value": "result_1"},
            {"label": "#2 (Línea T intensa)",       "value": "result_2"},
            {"label": "#3 (Línea T moderada)",      "value": "result_3"},
            {"label": "#4 (Línea T tenue)",         "value": "result_4"},
            {"label": "#5 (Sin línea T, solo línea C)", "value": "result_5"},
            {"label": "N/A (control no disponible)", "value": "na"},
        ],
    }],
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

JSON_POSITIVA = {
    "fixed_sample_type": "positive",
    "positions": [{
        "index": 0, "type": "select",
        "label": "Patrón Observado (PRB-01)",
        "instruction": "Seleccione el patrón visualizado.",
        "options": [
            {"label": "#1 (Línea T muy intensa)",  "value": "result_1"},
            {"label": "#2 (Línea T intensa)",       "value": "result_2"},
            {"label": "#3 (Línea T moderada)",      "value": "result_3"},
            {"label": "#4 (Línea T tenue)",         "value": "result_4"},
            {"label": "#5 (Sin línea T, solo línea C)", "value": "result_5"},
            {"label": "N/A (control no disponible)", "value": "na"},
        ],
    }],
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

    # 1. STBBM02 — JSON ya correcto, solo actualizar evaluation_type
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET evaluation_type = 'vama_multi_check', write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        JOIN amunet_quality_check_parameter p ON p.id = r.parameter_id
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE sc.product_parameter_rel_id = r.id
          AND p.code = 'MAVI-07'
          AND pt.default_code = 'STBBM02'
          AND sc.evaluation_type = 'mavi_07_ternary'
    """)
    rows_bbm02 = cr.rowcount
    _logger.info("STBBM02 MAVI-07: %d specs actualizadas a vama_multi_check", rows_bbm02)

    # 2. STBHE01 — cambia tipo y agrega JSON estándar de buffer
    for spec_name, json_data in [
        ('Muestra negativa', JSON_NEGATIVA),
        ('Muestra positiva', JSON_POSITIVA),
    ]:
        cr.execute("""
            UPDATE amunet_quality_parameter_specification_config sc
            SET evaluation_type     = 'vama_multi_check',
                text_phrase_mapping = %s,
                write_date          = NOW()
            FROM amunet_quality_parameter_product_rel r
            JOIN amunet_quality_check_parameter p ON p.id = r.parameter_id
            JOIN product_template pt ON pt.id = r.product_tmpl_id
            WHERE sc.product_parameter_rel_id = r.id
              AND p.code = 'MAVI-07'
              AND pt.default_code = 'STBHE01'
              AND sc.specification_name = %s
              AND sc.evaluation_type = 'mavi_07_ternary'
        """, (json.dumps(json_data, ensure_ascii=False), spec_name))
        _logger.info("STBHE01 MAVI-07 '%s': %d specs actualizadas", spec_name, cr.rowcount)
