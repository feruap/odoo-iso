# -*- coding: utf-8 -*-
"""
Normaliza SpecConf de 13 pruebas competitivas (antidoping / fentanilo):

  - MAVI-04 Letra adecuada: corrige 'Sellado adecuado' → 'Letra adecuada'
  - INC-002: opciones binarias (Contenido coincide / Contenido no coincide)
  - MAVI-07: asigna specification_name a los vama_multi_check sin nombre
  - MAVI-04: elimina duplicados de spec_id 691/692 sin nombre en DMADO02
  - MAVI-09 y MGA-0486 ya estaban correctos (2 y 1 activos respectivamente)
"""

COMPETITIVAS = (
    'DMACT02', 'DMADB01', 'DMADO02', 'DMADO03', 'DMADO04', 'DMADS01',
    'DMAMP02', 'DMCOC02', 'DMFEN01', 'DMMET02', 'DMOPI02', 'DMOPOI02',
    'DMTHC02',
)


def migrate(cr, version):
    placeholders = ','.join(['%s'] * len(COMPETITIVAS))

    # 1. MAVI-04 Letra adecuada: corregir opciones binarias
    cr.execute(f"""
        UPDATE amunet_quality_parameter_specification_config sc
        SET binary_prefix      = 'Letra adecuada/Letra inadecuada',
            binary_option_pass = 'Letra adecuada',
            binary_option_fail = 'Letra inadecuada'
        FROM amunet_quality_parameter_product_rel rel
        JOIN amunet_quality_check_parameter p ON p.id = rel.parameter_id
        JOIN product_template pt ON pt.id = rel.product_tmpl_id
        WHERE sc.product_parameter_rel_id = rel.id
          AND p.code = 'MAVI-04'
          AND sc.specification_name = 'Letra adecuada'
          AND sc.active = true
          AND pt.default_code IN ({placeholders})
          AND sc.binary_option_pass IS DISTINCT FROM 'Letra adecuada'
    """, COMPETITIVAS)

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
    """, COMPETITIVAS)

    # 3. MAVI-07: asignar specification_name según fixed_sample_type en JSON
    cr.execute(f"""
        UPDATE amunet_quality_parameter_specification_config sc
        SET specification_name = CASE
            WHEN sc.text_phrase_mapping::json->>'fixed_sample_type' = 'negative'
                 THEN 'Muestra negativa'
            WHEN sc.text_phrase_mapping::json->>'fixed_sample_type' = 'positive'
                 THEN 'Muestra positiva'
            END
        FROM amunet_quality_parameter_product_rel rel
        JOIN amunet_quality_check_parameter p ON p.id = rel.parameter_id
        JOIN product_template pt ON pt.id = rel.product_tmpl_id
        WHERE sc.product_parameter_rel_id = rel.id
          AND p.code = 'MAVI-07'
          AND pt.default_code IN ({placeholders})
          AND (sc.specification_name IS NULL OR sc.specification_name = '')
          AND sc.active = true
    """, COMPETITIVAS)

    # 4. MAVI-04 en competitivas: desactivar duplicados sin nombre
    #    (spec_id 691/692 repetidos que quedan cuando hay 7 en lugar de 5)
    cr.execute(f"""
        UPDATE amunet_quality_parameter_specification_config sc
        SET active = false
        FROM amunet_quality_parameter_product_rel rel
        JOIN amunet_quality_check_parameter p ON p.id = rel.parameter_id
        JOIN product_template pt ON pt.id = rel.product_tmpl_id
        WHERE sc.product_parameter_rel_id = rel.id
          AND p.code = 'MAVI-04'
          AND pt.default_code IN ({placeholders})
          AND (sc.specification_name IS NULL OR sc.specification_name = '')
          AND sc.active = true
    """, COMPETITIVAS)
