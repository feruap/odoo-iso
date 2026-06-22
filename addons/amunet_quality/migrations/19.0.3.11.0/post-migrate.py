import logging

_logger = logging.getLogger(__name__)

MAPPING_POSITIVE = (
    '{"fixed_sample_type":"positive","positions":[{"index":0,"type":"select",'
    '"label":"Patrón Observado (PRB-01)","instruction":"Seleccione el patrón visualizado.",'
    '"options":[{"label":"#1 (Línea T muy intensa)","value":"result_1"},'
    '{"label":"#2 (Línea T intensa)","value":"result_2"},'
    '{"label":"#3 (Línea T moderada)","value":"result_3"},'
    '{"label":"#4 (Línea T tenue)","value":"result_4"},'
    '{"label":"#5 (Sin línea T, solo línea C)","value":"result_5"},'
    '{"label":"N/A (control no disponible)","value":"na"}]}],'
    '"phrase_template":"Muestra positiva: Patrón {0}",'
    '"evaluation":{"rules":['
    '{"sample_type":"positive","result":"result_1","verdict":"pass","message":"Muestra Positiva: Patrón #1 - CUMPLE"},'
    '{"sample_type":"positive","result":"result_2","verdict":"pass","message":"Muestra Positiva: Patrón #2 - CUMPLE"},'
    '{"sample_type":"positive","result":"result_3","verdict":"pass","message":"Muestra Positiva: Patrón #3 - CUMPLE"},'
    '{"sample_type":"positive","result":"result_4","verdict":"pass","message":"Muestra Positiva: Patrón #4 - CUMPLE"},'
    '{"sample_type":"positive","result":"result_5","verdict":"fail","message":"Muestra Positiva: Patrón #5 (sin línea T) - NO CUMPLE"},'
    '{"sample_type":"positive","result":"na","verdict":"not_applicable","message":"Muestra Positiva: Control no disponible - N/A"}'
    ']}}'
)

MAPPING_NEGATIVE = (
    '{"fixed_sample_type":"negative","positions":[{"index":0,"type":"select",'
    '"label":"Patrón Observado (PRB-01)","instruction":"Seleccione el patrón visualizado.",'
    '"options":[{"label":"#1 (Línea T muy intensa)","value":"result_1"},'
    '{"label":"#2 (Línea T intensa)","value":"result_2"},'
    '{"label":"#3 (Línea T moderada)","value":"result_3"},'
    '{"label":"#4 (Línea T tenue)","value":"result_4"},'
    '{"label":"#5 (Sin línea T, solo línea C)","value":"result_5"},'
    '{"label":"N/A (control no disponible)","value":"na"}]}],'
    '"phrase_template":"Muestra negativa: Patrón {0}",'
    '"evaluation":{"rules":['
    '{"sample_type":"negative","result":"result_5","verdict":"pass","message":"Muestra Negativa: Patrón #5 (sin línea T) - CUMPLE"},'
    '{"sample_type":"negative","result":"result_1","verdict":"fail","message":"Muestra Negativa: Patrón #1 (línea T visible) - NO CUMPLE"},'
    '{"sample_type":"negative","result":"result_2","verdict":"fail","message":"Muestra Negativa: Patrón #2 (línea T visible) - NO CUMPLE"},'
    '{"sample_type":"negative","result":"result_3","verdict":"fail","message":"Muestra Negativa: Patrón #3 (línea T visible) - NO CUMPLE"},'
    '{"sample_type":"negative","result":"result_4","verdict":"fail","message":"Muestra Negativa: Patrón #4 (línea T visible) - NO CUMPLE"},'
    '{"sample_type":"negative","result":"na","verdict":"not_applicable","message":"Muestra Negativa: Control no disponible - N/A"}'
    ']}}'
)


def migrate(cr, version):
    """Migración 3.11.0: MAVI-07 fixed_sample_type para todas las hojas maestras cualitativas."""

    # 1. Actualizar Muestra positiva existentes bajo MAVI-07
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET text_phrase_mapping = %s,
            evaluation_type = 'vama_multi_check',
            write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        WHERE sc.product_parameter_rel_id = r.id
          AND r.parameter_code = 'MAVI-07'
          AND sc.specification_name = 'Muestra positiva'
          AND (sc.text_phrase_mapping IS NULL
               OR sc.text_phrase_mapping NOT LIKE '%%fixed_sample_type%%')
    """, (MAPPING_POSITIVE,))
    positiva_upd = cr.rowcount
    _logger.info("MAVI-07 migración: %d 'Muestra positiva' actualizados", positiva_upd)

    # 2. Actualizar Muestra negativa existentes bajo MAVI-07
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET text_phrase_mapping = %s,
            evaluation_type = 'vama_multi_check',
            write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        WHERE sc.product_parameter_rel_id = r.id
          AND r.parameter_code = 'MAVI-07'
          AND sc.specification_name = 'Muestra negativa'
          AND (sc.text_phrase_mapping IS NULL
               OR sc.text_phrase_mapping NOT LIKE '%%fixed_sample_type%%')
    """, (MAPPING_NEGATIVE,))
    negativa_upd = cr.rowcount
    _logger.info("MAVI-07 migración: %d 'Muestra negativa' actualizados", negativa_upd)

    # 3. Insertar Muestra positiva/negativa para hojas MAVI-07 que no los tengan
    cr.execute("""
        INSERT INTO amunet_quality_parameter_specification_config
            (product_parameter_rel_id, specification_id, specification_name,
             evaluation_type, sequence, active, create_date, write_date, text_phrase_mapping)
        SELECT
            r.id, 629, 'Muestra positiva', 'vama_multi_check', 1, true, NOW(), NOW(), %s
        FROM amunet_quality_parameter_product_rel r
        WHERE r.parameter_code = 'MAVI-07'
          AND NOT EXISTS (
              SELECT 1 FROM amunet_quality_parameter_specification_config sc2
              WHERE sc2.product_parameter_rel_id = r.id
                AND sc2.specification_name = 'Muestra positiva'
          )
    """, (MAPPING_POSITIVE,))
    pos_ins = cr.rowcount
    _logger.info("MAVI-07 migración: %d 'Muestra positiva' insertados", pos_ins)

    cr.execute("""
        INSERT INTO amunet_quality_parameter_specification_config
            (product_parameter_rel_id, specification_id, specification_name,
             evaluation_type, sequence, active, create_date, write_date, text_phrase_mapping)
        SELECT
            r.id, 628, 'Muestra negativa', 'vama_multi_check', 2, true, NOW(), NOW(), %s
        FROM amunet_quality_parameter_product_rel r
        WHERE r.parameter_code = 'MAVI-07'
          AND NOT EXISTS (
              SELECT 1 FROM amunet_quality_parameter_specification_config sc2
              WHERE sc2.product_parameter_rel_id = r.id
                AND sc2.specification_name = 'Muestra negativa'
          )
    """, (MAPPING_NEGATIVE,))
    neg_ins = cr.rowcount
    _logger.info("MAVI-07 migración: %d 'Muestra negativa' insertados", neg_ins)

    _logger.info(
        "MAVI-07 migración completa: %d actualizados, %d insertados",
        positiva_upd + negativa_upd,
        pos_ins + neg_ins
    )
