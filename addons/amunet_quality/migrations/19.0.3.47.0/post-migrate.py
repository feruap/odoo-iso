# -*- coding: utf-8 -*-
"""
DMPSA01, DMTSH02, DMFRT02 — reemplaza MAVI-07 cualitativo por MAVI-15 semicuantitativo.

1. Crea plantillas (amunet_quality_check_parameter_specification) para
   "Control negativo" y "Control positivo" en MAVI-15 si no existen.
2. Desactiva specs MAVI-07 'mavi_07_ternary' (Muestra negativa/positiva).
3. Crea relación producto-MAVI-15 si no existe.
4. Agrega dos specs vama_multi_check con opciones Bajo/Intermedio/Alto:
   - Control negativo: Bajo = CUMPLE
   - Control positivo: Intermedio o Alto = CUMPLE
"""
import json

PRODUCTOS = ('DMPSA01', 'DMTSH02', 'DMFRT02')
MAVI15_PARAM_ID = 147

JSON_NEG = {
    "fixed_sample_type": "negative",
    "positions": [{"index": 0, "type": "select",
        "label": "Intensidad observada (PRS-01)",
        "instruction": "Seleccione el nivel de la línea T respecto a la línea R.",
        "options": [
            {"label": "Bajo: C+R visibles, T no visible", "value": "bajo"},
            {"label": "Intermedio: C+R+T visibles, T≈R",  "value": "intermedio"},
            {"label": "Alto: C+T visibles, T>R",           "value": "alto"},
        ]}],
    "phrase_template": "Control negativo: {0}",
    "evaluation": {"rules": [
        {"sample_type": "negative", "result": "bajo",
         "verdict": "pass",
         "message": "Control negativo: Bajo (T no visible) — CUMPLE"},
        {"sample_type": "negative", "result": "intermedio",
         "verdict": "fail",
         "message": "Control negativo: Intermedio — NO CUMPLE"},
        {"sample_type": "negative", "result": "alto",
         "verdict": "fail",
         "message": "Control negativo: Alto — NO CUMPLE"},
    ]},
}

JSON_POS = {
    "fixed_sample_type": "positive",
    "positions": [
        {
            "index": 0, "type": "select",
            "label": "Positivo bajo — intensidad de la línea T",
            "instruction": "Seleccione el nivel de la línea T respecto a la línea R.",
            "pass_value": "intermedio",
            "options": [
                {"label": "Bajo: C+R visibles, T no visible", "value": "bajo"},
                {"label": "Intermedio: C+R+T visibles, T≈R",  "value": "intermedio"},
                {"label": "Alto: C+T visibles, T>R",           "value": "alto"},
            ]
        },
        {
            "index": 1, "type": "select",
            "label": "Positivo alto — intensidad de la línea T",
            "instruction": "Seleccione el nivel de la línea T respecto a la línea R.",
            "pass_value": "alto",
            "options": [
                {"label": "Bajo: C+R visibles, T no visible", "value": "bajo"},
                {"label": "Intermedio: C+R+T visibles, T≈R",  "value": "intermedio"},
                {"label": "Alto: C+T visibles, T>R",           "value": "alto"},
            ]
        }
    ],
    "phrase_template": "Control positivo bajo: {0} / Control positivo alto: {1}",
    "success_message": "Control positivo: Positivo bajo=Intermedio y Positivo alto=Alto — CUMPLE",
    "error_prefix": "Control positivo NO CUMPLE:",
}


def _get_or_create_spec_template(cr, logger, param_id, name, json_data):
    """Devuelve el id de la plantilla de spec; la crea si no existe."""
    cr.execute("""
        SELECT id FROM amunet_quality_check_parameter_specification
        WHERE parameter_id = %s AND name = %s AND evaluation_type = 'vama_multi_check'
        LIMIT 1
    """, (param_id, name))
    row = cr.fetchone()
    if row:
        return row[0]
    cr.execute("""
        INSERT INTO amunet_quality_check_parameter_specification
            (parameter_id, name, evaluation_type, text_phrase_mapping,
             acceptance_criteria, active, create_date, write_date, create_uid, write_uid)
        VALUES (%s, %s, 'vama_multi_check', %s,
                'Resultado coincide con el control de referencia (PRS-01)',
                true, NOW(), NOW(), 1, 1)
        RETURNING id
    """, (param_id, name, json.dumps(json_data, ensure_ascii=False)))
    spec_id = cr.fetchone()[0]
    logger.info("MAVI-15 plantilla '%s' creada (id=%d)", name, spec_id)
    return spec_id


def migrate(cr, version):
    import logging
    _logger = logging.getLogger(__name__)
    ph = ','.join(['%s'] * len(PRODUCTOS))

    # 1. Crear plantillas de spec para MAVI-15
    spec_neg_id = _get_or_create_spec_template(cr, _logger, MAVI15_PARAM_ID,
                                               'Control negativo', JSON_NEG)
    spec_pos_id = _get_or_create_spec_template(cr, _logger, MAVI15_PARAM_ID,
                                               'Control positivo', JSON_POS)

    # 2. Desactivar rel MAVI-07 completo y rels VAMA para las 3 semicuantitativas
    cr.execute(f"""
        UPDATE amunet_quality_parameter_product_rel r
        SET active = false, write_date = NOW()
        FROM amunet_quality_check_parameter p,
             product_template pt
        WHERE p.id = r.parameter_id
          AND pt.id = r.product_tmpl_id
          AND p.code IN ('MAVI-07','VAMA-034','VAMA-036','VAMA-064','VAMA-091')
          AND pt.default_code IN ({ph})
          AND r.active = true
    """, PRODUCTOS)
    _logger.info("Rels MAVI-07 y VAMA desactivados: %d", cr.rowcount)

    # 3. Para cada producto: vincular MAVI-15 y crear specs
    cr.execute(f"SELECT id, default_code FROM product_template WHERE default_code IN ({ph})",
               PRODUCTOS)
    productos = {r[1]: r[0] for r in cr.fetchall()}

    for code, tmpl_id in productos.items():
        # Crear rel producto-MAVI-15 si no existe
        cr.execute("""
            SELECT id FROM amunet_quality_parameter_product_rel
            WHERE product_tmpl_id = %s AND parameter_id = %s
        """, (tmpl_id, MAVI15_PARAM_ID))
        rel_row = cr.fetchone()
        if rel_row:
            rel_id = rel_row[0]
        else:
            cr.execute("""
                INSERT INTO amunet_quality_parameter_product_rel
                    (product_tmpl_id, parameter_id, parameter_code, display_name,
                     active, sequence, active_spec_count,
                     create_date, write_date, create_uid, write_uid)
                VALUES (%s, %s, 'MAVI-15',
                        '[MAVI-15] Visualización de líneas semicuantitativas',
                        true, 10, 2,
                        NOW(), NOW(), 1, 1)
                RETURNING id
            """, (tmpl_id, MAVI15_PARAM_ID))
            rel_id = cr.fetchone()[0]
            _logger.info("%s: rel MAVI-15 creada (id=%d)", code, rel_id)

        # Crear specs Control negativo y Control positivo si no existen
        for spec_tmpl_id, spec_name, json_data in [
            (spec_neg_id, 'Control negativo', JSON_NEG),
            (spec_pos_id, 'Control positivo', JSON_POS),
        ]:
            cr.execute("""
                SELECT id FROM amunet_quality_parameter_specification_config
                WHERE product_parameter_rel_id = %s AND specification_id = %s
            """, (rel_id, spec_tmpl_id))
            if not cr.fetchone():
                cr.execute("""
                    INSERT INTO amunet_quality_parameter_specification_config
                        (product_parameter_rel_id, specification_id,
                         specification_name, evaluation_type,
                         text_phrase_mapping, acceptance_criteria,
                         active, sequence, create_date, write_date, create_uid, write_uid)
                    VALUES (%s, %s, %s, 'vama_multi_check', %s,
                            'Resultado coincide con el control de referencia (PRS-01)',
                            true, 10, NOW(), NOW(), 1, 1)
                """, (rel_id, spec_tmpl_id, spec_name,
                      json.dumps(json_data, ensure_ascii=False)))
                _logger.info("%s: spec MAVI-15 '%s' creada", code, spec_name)
