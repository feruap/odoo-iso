# -*- coding: utf-8 -*-
"""
Normaliza SpecConf de 49 pruebas cualitativas y 13 competitivas (antidoping)
para alinearlas con la plantilla DMHBA01 (hemoglobina):

  - MAVI-04 Letra adecuada: opciones binarias correctas (ya no dice 'Sellado')
  - INC-002: opciones binarias (Contenido coincide / Contenido no coincide)
  - MAVI-09: deja solo 2 activos por producto (Liberación 1-30s + Migración 30-180s)
  - MGA-0486: deja solo 1 activo por producto (Prueba de colorante)
  - MAVI-07: reemplaza todos los anteriores por 2 vama_multi_check correctos
    (Muestra negativa patrón #5 cumple / Muestra positiva patrones #1-#4 cumple)
"""

import json

CUALITATIVAS = (
    'DMAFP01', 'DMATB01', 'DMCAL01', 'DMCAM01', 'DMCAN01', 'DMCAO01',
    'DMCAP01', 'DMCBR01', 'DMCHA01', 'DMCHI01', 'DMCLAM01', 'DMCRD01',
    'DMDCZ01', 'DMDEN01', 'DMDEN02', 'DMDMD01', 'DMENG01', 'DMENT01',
    'DMESC01', 'DMFFN01', 'DMFRE01', 'DMGIA01', 'DMGON01', 'DMHCG01',
    'DMHCG02', 'DMHCG03', 'DMHPY02', 'DMIAB01', 'DMIAM01', 'DMMCT01',
    'DMMON01', 'DMMYC01', 'DMPRO01', 'DMRAV01', 'DMSAT01', 'DMSGF01',
    'DMSPN01', 'DMSPN02', 'DMSPO01', 'DMSVI01', 'DMTET01', 'DMTIF01',
    'DMTOR02', 'DMTRF01', 'DMTSH01', 'DMVIH01', 'DMVIH02', 'DMVSR01',
    'DMZIK01',
)

MAVI07_NEGATIVA = {
    "fixed_sample_type": "negative",
    "positions": [{"index": 0, "type": "select", "label": "Patrón Observado",
        "instruction": "Seleccione el patrón visualizado.",
        "options": [
            {"label": "#1 (Línea T muy intensa)", "value": "result_1"},
            {"label": "#2 (Línea T intensa)", "value": "result_2"},
            {"label": "#3 (Línea T moderada)", "value": "result_3"},
            {"label": "#4 (Línea T tenue)", "value": "result_4"},
            {"label": "#5 (Sin línea T, solo línea C)", "value": "result_5"},
            {"label": "#6 (Sin línea C, con línea T)", "value": "result_6"},
            {"label": "#7 (Sin línea C ni línea T)", "value": "result_7"},
            {"label": "N/A (control no disponible)", "value": "na"},
        ]}],
    "phrase_template": "Muestra negativa: Patrón {0}",
    "evaluation": {"rules": [
        {"sample_type": "negative", "result": "result_5", "verdict": "pass",
         "message": "Muestra Negativa: Patrón #5 — Visualización solo de línea control — CUMPLE"},
        {"sample_type": "negative", "result": "result_1", "verdict": "fail",
         "message": "Muestra Negativa: Patrón #1 (línea T visible) — NO CUMPLE"},
        {"sample_type": "negative", "result": "result_2", "verdict": "fail",
         "message": "Muestra Negativa: Patrón #2 (línea T visible) — NO CUMPLE"},
        {"sample_type": "negative", "result": "result_3", "verdict": "fail",
         "message": "Muestra Negativa: Patrón #3 (línea T visible) — NO CUMPLE"},
        {"sample_type": "negative", "result": "result_4", "verdict": "fail",
         "message": "Muestra Negativa: Patrón #4 (línea T visible) — NO CUMPLE"},
        {"sample_type": "negative", "result": "result_6", "verdict": "fail",
         "message": "Muestra Negativa: Patrón #6 (sin línea C) — NO CUMPLE"},
        {"sample_type": "negative", "result": "result_7", "verdict": "fail",
         "message": "Muestra Negativa: Patrón #7 (sin línea C ni T) — NO CUMPLE"},
        {"sample_type": "negative", "result": "na", "verdict": "not_applicable",
         "message": "Muestra Negativa: Control no disponible — N/A"},
    ]},
}

MAVI07_POSITIVA = {
    "fixed_sample_type": "positive",
    "positions": [{"index": 0, "type": "select", "label": "Patrón Observado",
        "instruction": "Seleccione el patrón visualizado.",
        "options": [
            {"label": "#1 (Línea T muy intensa)", "value": "result_1"},
            {"label": "#2 (Línea T intensa)", "value": "result_2"},
            {"label": "#3 (Línea T moderada)", "value": "result_3"},
            {"label": "#4 (Línea T tenue)", "value": "result_4"},
            {"label": "#5 (Sin línea T, solo línea C)", "value": "result_5"},
            {"label": "#6 (Sin línea C, con línea T)", "value": "result_6"},
            {"label": "#7 (Sin línea C ni línea T)", "value": "result_7"},
            {"label": "N/A (control no disponible)", "value": "na"},
        ]}],
    "phrase_template": "Muestra positiva: Patrón {0}",
    "evaluation": {"rules": [
        {"sample_type": "positive", "result": "result_1", "verdict": "pass",
         "message": "Muestra Positiva: Patrón #1 — Visualización línea control y línea de prueba — CUMPLE"},
        {"sample_type": "positive", "result": "result_2", "verdict": "pass",
         "message": "Muestra Positiva: Patrón #2 — Visualización línea control y línea de prueba — CUMPLE"},
        {"sample_type": "positive", "result": "result_3", "verdict": "pass",
         "message": "Muestra Positiva: Patrón #3 — Visualización línea control y línea de prueba — CUMPLE"},
        {"sample_type": "positive", "result": "result_4", "verdict": "pass",
         "message": "Muestra Positiva: Patrón #4 — Visualización línea control y línea de prueba — CUMPLE"},
        {"sample_type": "positive", "result": "result_5", "verdict": "fail",
         "message": "Muestra Positiva: Patrón #5 (sin línea T) — NO CUMPLE"},
        {"sample_type": "positive", "result": "result_6", "verdict": "fail",
         "message": "Muestra Positiva: Patrón #6 (sin línea C) — NO CUMPLE"},
        {"sample_type": "positive", "result": "result_7", "verdict": "fail",
         "message": "Muestra Positiva: Patrón #7 (sin línea C ni T) — NO CUMPLE"},
        {"sample_type": "positive", "result": "na", "verdict": "not_applicable",
         "message": "Muestra Positiva: Control no disponible — N/A"},
    ]},
}


def migrate(cr, version):
    placeholders = ','.join(['%s'] * len(CUALITATIVAS))

    # 1. MAVI-04: corregir Letra adecuada (antes podía decir 'Sellado')
    cr.execute(f"""
        UPDATE amunet_quality_parameter_specification_config sc
        SET specification_name   = 'Letra adecuada',
            binary_prefix        = 'Letra adecuada/Letra inadecuada',
            binary_option_pass   = 'Letra adecuada',
            binary_option_fail   = 'Letra inadecuada',
            acceptance_criteria  = 'Letra adecuada'
        FROM amunet_quality_parameter_product_rel rel
        JOIN amunet_quality_check_parameter p ON p.id = rel.parameter_id
        JOIN product_template pt ON pt.id = rel.product_tmpl_id
        WHERE sc.product_parameter_rel_id = rel.id
          AND p.code = 'MAVI-04'
          AND pt.default_code IN ({placeholders})
          AND sc.specification_name IN ('Sellado', 'Letra adecuada')
          AND sc.binary_prefix != 'Letra adecuada/Letra inadecuada'
    """, CUALITATIVAS)

    # 2. INC-002: opciones binarias de contenido
    cr.execute(f"""
        UPDATE amunet_quality_parameter_specification_config sc
        SET binary_prefix        = 'Contenido coincide/Contenido no coincide',
            binary_option_pass   = 'Contenido coincide',
            binary_option_fail   = 'Contenido no coincide',
            acceptance_criteria  = 'Coincidencia con el contenido especificado en el manual vigente.'
        FROM amunet_quality_parameter_product_rel rel
        JOIN amunet_quality_check_parameter p ON p.id = rel.parameter_id
        JOIN product_template pt ON pt.id = rel.product_tmpl_id
        WHERE sc.product_parameter_rel_id = rel.id
          AND p.code = 'INC-002'
          AND pt.default_code IN ({placeholders})
          AND (sc.binary_prefix IS NULL OR sc.binary_prefix = '')
    """, CUALITATIVAS)

    # 3. MAVI-09: desactivar todos, reactivar solo Liberación y Migración correctos
    cr.execute(f"""
        UPDATE amunet_quality_parameter_specification_config sc
        SET active = false
        FROM amunet_quality_parameter_product_rel rel
        JOIN amunet_quality_check_parameter p ON p.id = rel.parameter_id
        JOIN product_template pt ON pt.id = rel.product_tmpl_id
        WHERE sc.product_parameter_rel_id = rel.id
          AND p.code = 'MAVI-09'
          AND pt.default_code IN ({placeholders})
    """, CUALITATIVAS)

    cr.execute(f"""
        WITH min_lib AS (
            SELECT MIN(sc.id) AS sc_id
            FROM amunet_quality_parameter_specification_config sc
            JOIN amunet_quality_parameter_product_rel rel ON sc.product_parameter_rel_id = rel.id
            JOIN amunet_quality_check_parameter p ON p.id = rel.parameter_id
            JOIN product_template pt ON pt.id = rel.product_tmpl_id
            WHERE p.code = 'MAVI-09'
              AND pt.default_code IN ({placeholders})
              AND sc.specification_name = 'Liberación de conjugado'
            GROUP BY rel.product_tmpl_id
        )
        UPDATE amunet_quality_parameter_specification_config sc
        SET active = true,
            specification_name  = 'Liberación de conjugado',
            acceptance_criteria = '1-30 segundos'
        FROM min_lib WHERE sc.id = min_lib.sc_id
    """, CUALITATIVAS)

    cr.execute(f"""
        WITH min_mig AS (
            SELECT MIN(sc.id) AS sc_id
            FROM amunet_quality_parameter_specification_config sc
            JOIN amunet_quality_parameter_product_rel rel ON sc.product_parameter_rel_id = rel.id
            JOIN amunet_quality_check_parameter p ON p.id = rel.parameter_id
            JOIN product_template pt ON pt.id = rel.product_tmpl_id
            WHERE p.code = 'MAVI-09'
              AND pt.default_code IN ({placeholders})
              AND sc.specification_name = 'Migración de conjugado'
            GROUP BY rel.product_tmpl_id
        )
        UPDATE amunet_quality_parameter_specification_config sc
        SET active = true,
            specification_name  = 'Migración de conjugado',
            acceptance_criteria = '30-180 segundos'
        FROM min_mig WHERE sc.id = min_mig.sc_id
    """, CUALITATIVAS)

    # 4. MGA-0486: desactivar todos, reactivar solo "Prueba de colorante"
    cr.execute(f"""
        UPDATE amunet_quality_parameter_specification_config sc
        SET active = false
        FROM amunet_quality_parameter_product_rel rel
        JOIN amunet_quality_check_parameter p ON p.id = rel.parameter_id
        JOIN product_template pt ON pt.id = rel.product_tmpl_id
        WHERE sc.product_parameter_rel_id = rel.id
          AND p.code = 'MGA-0486'
          AND pt.default_code IN ({placeholders})
    """, CUALITATIVAS)

    cr.execute(f"""
        WITH min_mga AS (
            SELECT MIN(sc.id) AS sc_id
            FROM amunet_quality_parameter_specification_config sc
            JOIN amunet_quality_parameter_product_rel rel ON sc.product_parameter_rel_id = rel.id
            JOIN amunet_quality_check_parameter p ON p.id = rel.parameter_id
            JOIN product_template pt ON pt.id = rel.product_tmpl_id
            WHERE p.code = 'MGA-0486'
              AND pt.default_code IN ({placeholders})
            GROUP BY rel.product_tmpl_id
        )
        UPDATE amunet_quality_parameter_specification_config sc
        SET active = true,
            specification_name  = 'Prueba de colorante',
            acceptance_criteria = 'Ausencia de colorante'
        FROM min_mga WHERE sc.id = min_mga.sc_id
    """, CUALITATIVAS)

    # 5. MAVI-07: desactivar todos los existentes e insertar 2 correctos por producto
    cr.execute(f"""
        UPDATE amunet_quality_parameter_specification_config sc
        SET active = false
        FROM amunet_quality_parameter_product_rel rel
        JOIN amunet_quality_check_parameter p ON p.id = rel.parameter_id
        JOIN product_template pt ON pt.id = rel.product_tmpl_id
        WHERE sc.product_parameter_rel_id = rel.id
          AND p.code = 'MAVI-07'
          AND pt.default_code IN ({placeholders})
          AND sc.evaluation_type != 'vama_multi_check'
    """, CUALITATIVAS)

    # Insertar Muestra negativa solo si no existe ya uno correcto
    negativa_json = json.dumps(MAVI07_NEGATIVA, ensure_ascii=False)
    cr.execute(f"""
        INSERT INTO amunet_quality_parameter_specification_config
          (product_parameter_rel_id, specification_id, specification_name,
           evaluation_type, acceptance_criteria, active, text_phrase_mapping,
           create_uid, write_uid, create_date, write_date)
        SELECT rel.id, 628, 'Muestra negativa', 'vama_multi_check',
               'Visualización solo de línea control, patrón #5',
               true, %s, 1, 1, NOW(), NOW()
        FROM amunet_quality_parameter_product_rel rel
        JOIN amunet_quality_check_parameter p ON p.id = rel.parameter_id
        JOIN product_template pt ON pt.id = rel.product_tmpl_id
        WHERE p.code = 'MAVI-07'
          AND pt.default_code IN ({placeholders})
          AND NOT EXISTS (
              SELECT 1 FROM amunet_quality_parameter_specification_config sc2
              WHERE sc2.product_parameter_rel_id = rel.id
                AND sc2.evaluation_type = 'vama_multi_check'
                AND sc2.specification_name = 'Muestra negativa'
                AND sc2.active = true
          )
    """, [negativa_json] + list(CUALITATIVAS))

    positiva_json = json.dumps(MAVI07_POSITIVA, ensure_ascii=False)
    cr.execute(f"""
        INSERT INTO amunet_quality_parameter_specification_config
          (product_parameter_rel_id, specification_id, specification_name,
           evaluation_type, acceptance_criteria, active, text_phrase_mapping,
           create_uid, write_uid, create_date, write_date)
        SELECT rel.id, 629, 'Muestra positiva', 'vama_multi_check',
               'Visualización línea control y línea de prueba, patrón #1-#4',
               true, %s, 1, 1, NOW(), NOW()
        FROM amunet_quality_parameter_product_rel rel
        JOIN amunet_quality_check_parameter p ON p.id = rel.parameter_id
        JOIN product_template pt ON pt.id = rel.product_tmpl_id
        WHERE p.code = 'MAVI-07'
          AND pt.default_code IN ({placeholders})
          AND NOT EXISTS (
              SELECT 1 FROM amunet_quality_parameter_specification_config sc2
              WHERE sc2.product_parameter_rel_id = rel.id
                AND sc2.evaluation_type = 'vama_multi_check'
                AND sc2.specification_name = 'Muestra positiva'
                AND sc2.active = true
          )
    """, [positiva_json] + list(CUALITATIVAS))
