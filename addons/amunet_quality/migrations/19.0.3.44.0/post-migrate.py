# -*- coding: utf-8 -*-
"""
STBPR02 y STBPR04: corrige el JSON de MAVI-07 para que use fixed_sample_type
(igual que STBPR01 y STBPR03). Elimina el doble dropdown que pedía seleccionar
"Muestra Negativa/Positiva" primero (era el "negativo extra" que sobraba).
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
            {"label": "N/A (control no disponible)",   "value": "na"},
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
            {"label": "N/A (control no disponible)",   "value": "na"},
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

PRODUCTOS = ('STBPR02', 'STBPR04')


def migrate(cr, version):
    import logging
    _logger = logging.getLogger(__name__)
    ph = ','.join(['%s'] * len(PRODUCTOS))

    for spec_name, json_data in [('Muestra negativa', JSON_NEG), ('Muestra positiva', JSON_POS)]:
        cr.execute(f"""
            UPDATE amunet_quality_parameter_specification_config sc
            SET text_phrase_mapping = %s::jsonb, write_date = NOW()
            FROM amunet_quality_parameter_product_rel r
            JOIN amunet_quality_check_parameter p ON p.id = r.parameter_id
            JOIN product_template pt ON pt.id = r.product_tmpl_id
            WHERE sc.product_parameter_rel_id = r.id
              AND p.code = 'MAVI-07' AND sc.active = true
              AND sc.specification_name = %s
              AND pt.default_code IN ({ph})
        """, (json.dumps(json_data, ensure_ascii=False), spec_name, *PRODUCTOS))
        _logger.info("STBPR02/04 MAVI-07 '%s': %d specs actualizadas", spec_name, cr.rowcount)
