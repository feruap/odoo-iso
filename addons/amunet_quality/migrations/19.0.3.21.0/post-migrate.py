import json
import logging

_logger = logging.getLogger(__name__)

COMPETITIVE_CODES = (
    'SPHMC04',   # Albúmina cualitativa
    'SPHMC10',   # Marihuana (THC) en orina
    'SPHMC11',   # Anfetamina (AMP) en orina
    'SPHMC12',   # Cocaína (COC) en orina
    'SPHMC13',   # Metanfetamina (MET) en orina
    'SPHMC14',   # Opiáceos (OPI) en orina
    'SPHMC53',   # Antidoping Saliva 2P
    'SPHMC54',   # Antidoping Saliva 3P
)

OPTIONS = [
    {"label": "#1 (Línea T muy intensa)",          "value": "result_1"},
    {"label": "#2 (Línea T intensa)",              "value": "result_2"},
    {"label": "#3 (Línea T moderada)",             "value": "result_3"},
    {"label": "#4 (Línea T tenue)",                "value": "result_4"},
    {"label": "#5 (Sin línea T, solo línea C)",    "value": "result_5"},
    {"label": "#6 (Sin línea C, con línea T visible)", "value": "result_6"},
    {"label": "#7 (Sin línea C ni línea T)",       "value": "result_7"},
    {"label": "N/A (control no disponible)",       "value": "na"},
]

POSITION = {
    "index": 0,
    "type": "select",
    "label": "Patrón Observado (PRB-01)",
    "instruction": "Seleccione el patrón visualizado.",
    "options": OPTIONS,
}

# Competitiva positiva: solo C (sin T) = CUMPLE; C+T = NO CUMPLE
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

# Competitiva negativa: C+T visibles = CUMPLE; solo C = NO CUMPLE
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


def migrate(cr, version):
    """Migración 3.21.0: MAVI-07 competitivo para hojas cualitativas/competitivas.

    Invierte los veredictos respecto a las cualitativas estándar:
    - Positiva: solo C (patrón #5) = CUMPLE; C+T = NO CUMPLE
    - Negativa: C+T (#1-#4) = CUMPLE; solo C = NO CUMPLE
    """
    # 1. Actualizar spec_configs activos
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET text_phrase_mapping = CASE
              WHEN sc.specification_name = 'Muestra positiva' THEN %s::jsonb
              WHEN sc.specification_name = 'Muestra negativa' THEN %s::jsonb
            END,
            write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE sc.product_parameter_rel_id = r.id
          AND r.parameter_code = 'MAVI-07'
          AND sc.specification_name IN ('Muestra positiva', 'Muestra negativa')
          AND sc.active = true
          AND pt.default_code = ANY(%s)
    """, (MAPPING_POSITIVE, MAPPING_NEGATIVE, list(COMPETITIVE_CODES)))
    sc_updated = cr.rowcount

    # 2. Sincronizar checks abiertos
    cr.execute("""
        UPDATE amunet_quality_test_line_detail tld
        SET text_phrase_mapping = CASE
              WHEN tld.name = 'Muestra positiva' THEN %s::jsonb
              WHEN tld.name = 'Muestra negativa' THEN %s::jsonb
            END,
            write_date = NOW()
        FROM amunet_quality_parameter_specification_config sc,
             amunet_quality_parameter_product_rel r,
             product_template pt,
             amunet_quality_test_line tl,
             amunet_quality_check qc,
             product_product pp
        WHERE tld.specification_config_id = sc.id
          AND sc.product_parameter_rel_id = r.id
          AND r.product_tmpl_id = pt.id
          AND tld.test_line_id = tl.id
          AND tl.check_id = qc.id
          AND qc.product_id = pp.id
          AND pp.product_tmpl_id = pt.id
          AND r.parameter_code = 'MAVI-07'
          AND tld.name IN ('Muestra positiva', 'Muestra negativa')
          AND qc.state IN ('draft', 'in_progress')
          AND pt.default_code = ANY(%s)
    """, (MAPPING_POSITIVE, MAPPING_NEGATIVE, list(COMPETITIVE_CODES)))
    det_updated = cr.rowcount

    _logger.info(
        "Migración 3.21.0 — MAVI-07 competitivo aplicado a %s: spec_configs=%d, detalles=%d",
        COMPETITIVE_CODES, sc_updated, det_updated,
    )
