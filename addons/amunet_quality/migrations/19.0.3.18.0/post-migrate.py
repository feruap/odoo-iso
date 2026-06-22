import logging

_logger = logging.getLogger(__name__)

SPHM_CODES = (
    'SPHMC01','SPHMC02','SPHMC03','SPHMC04','SPHMC05','SPHMC06','SPHMC08',
    'SPHMC15','SPHMC17','SPHMC20','SPHMC21','SPHMC22','SPHMC23','SPHMC24',
    'SPHMC27','SPHMC28','SPHMC29','SPHMC30','SPHMC31','SPHMC32','SPHMC33',
    'SPHMC35','SPHMC36','SPHMC37','SPHMC39','SPHMC40','SPHMC41','SPHMC42',
    'SPHMC43','SPHMC44','SPHMC45','SPHMC46','SPHMC47','SPHMC48','SPHMC49',
    'SPHMC50','SPHMC51','SPHMC55','SPHMC56','SPHMC57','SPHMC58','SPHMC59',
    'SPHMC60','SPHMC61','SPHMC62','SPHMC64','SPHMC65','SPHMC66','SPHMC69',
    'SPHMC70','SPHMC71','SPHMC72','SPHMC73','SPHMC74',
    'SPHMT01','SPHMT03','SPHMT04','SPHMT05','SPHMT06',
)

_OPTIONS = (
    '{"label":"#1 (Línea T muy intensa)","value":"result_1"},'
    '{"label":"#2 (Línea T intensa)","value":"result_2"},'
    '{"label":"#3 (Línea T moderada)","value":"result_3"},'
    '{"label":"#4 (Línea T tenue)","value":"result_4"},'
    '{"label":"#5 (Sin línea T, solo línea C)","value":"result_5"},'
    '{"label":"#6 (Sin línea C, con línea T visible)","value":"result_6"},'
    '{"label":"#7 (Sin línea C ni línea T)","value":"result_7"},'
    '{"label":"N/A (control no disponible)","value":"na"}'
)

_POS_BASE = (
    '{"index":0,"type":"select","label":"Patrón Observado (PRB-01)",'
    '"instruction":"Seleccione el patrón visualizado.","options":[' + _OPTIONS + ']}'
)

# Muestra positiva: #1-#4 CUMPLE | #5-#7 NO CUMPLE | N/A
MAPPING_POSITIVE = (
    '{"fixed_sample_type":"positive","positions":[' + _POS_BASE + '],'
    '"phrase_template":"Muestra positiva: Patrón {0}",'
    '"evaluation":{"rules":['
    '{"sample_type":"positive","result":"result_1","verdict":"pass","message":"Muestra Positiva: Patrón #1 - CUMPLE"},'
    '{"sample_type":"positive","result":"result_2","verdict":"pass","message":"Muestra Positiva: Patrón #2 - CUMPLE"},'
    '{"sample_type":"positive","result":"result_3","verdict":"pass","message":"Muestra Positiva: Patrón #3 - CUMPLE"},'
    '{"sample_type":"positive","result":"result_4","verdict":"pass","message":"Muestra Positiva: Patrón #4 - CUMPLE"},'
    '{"sample_type":"positive","result":"result_5","verdict":"fail","message":"Muestra Positiva: Patrón #5 (sin línea T) - NO CUMPLE"},'
    '{"sample_type":"positive","result":"result_6","verdict":"fail","message":"Muestra Positiva: Patrón #6 (sin línea C) - NO CUMPLE"},'
    '{"sample_type":"positive","result":"result_7","verdict":"fail","message":"Muestra Positiva: Patrón #7 (sin línea C ni T) - NO CUMPLE"},'
    '{"sample_type":"positive","result":"na","verdict":"not_applicable","message":"Muestra Positiva: Control no disponible - N/A"}'
    ']}}'
)

# Muestra negativa: #5 CUMPLE | #1-#4, #6, #7 NO CUMPLE | N/A
MAPPING_NEGATIVE = (
    '{"fixed_sample_type":"negative","positions":[' + _POS_BASE + '],'
    '"phrase_template":"Muestra negativa: Patrón {0}",'
    '"evaluation":{"rules":['
    '{"sample_type":"negative","result":"result_5","verdict":"pass","message":"Muestra Negativa: Patrón #5 (sin línea T) - CUMPLE"},'
    '{"sample_type":"negative","result":"result_1","verdict":"fail","message":"Muestra Negativa: Patrón #1 (línea T visible) - NO CUMPLE"},'
    '{"sample_type":"negative","result":"result_2","verdict":"fail","message":"Muestra Negativa: Patrón #2 (línea T visible) - NO CUMPLE"},'
    '{"sample_type":"negative","result":"result_3","verdict":"fail","message":"Muestra Negativa: Patrón #3 (línea T visible) - NO CUMPLE"},'
    '{"sample_type":"negative","result":"result_4","verdict":"fail","message":"Muestra Negativa: Patrón #4 (línea T visible) - NO CUMPLE"},'
    '{"sample_type":"negative","result":"result_6","verdict":"fail","message":"Muestra Negativa: Patrón #6 (sin línea C) - NO CUMPLE"},'
    '{"sample_type":"negative","result":"result_7","verdict":"fail","message":"Muestra Negativa: Patrón #7 (sin línea C ni T) - NO CUMPLE"},'
    '{"sample_type":"negative","result":"na","verdict":"not_applicable","message":"Muestra Negativa: Control no disponible - N/A"}'
    ']}}'
)


def migrate(cr, version):
    """Migración 3.18.0: MAVI-07 — patrones #6 y #7 pasan de INVÁLIDA a NO CUMPLE.
    Una prueba sin línea de control no cumple; se equipara a fallo, no a invalidez.
    """
    # Actualizar spec_configs Muestra positiva
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET text_phrase_mapping = %s, write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE sc.product_parameter_rel_id = r.id
          AND r.parameter_code = 'MAVI-07'
          AND sc.specification_name = 'Muestra positiva'
          AND sc.active = true
          AND pt.default_code = ANY(%s)
    """, (MAPPING_POSITIVE, list(SPHM_CODES)))
    pos_sc = cr.rowcount

    # Actualizar spec_configs Muestra negativa
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET text_phrase_mapping = %s, write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE sc.product_parameter_rel_id = r.id
          AND r.parameter_code = 'MAVI-07'
          AND sc.specification_name = 'Muestra negativa'
          AND sc.active = true
          AND pt.default_code = ANY(%s)
    """, (MAPPING_NEGATIVE, list(SPHM_CODES)))
    neg_sc = cr.rowcount

    # Propagar a checks abiertos — positiva
    cr.execute("""
        UPDATE amunet_quality_test_line_detail tld
        SET text_phrase_mapping = %s, write_date = NOW()
        FROM amunet_quality_test_line tl,
             amunet_quality_check qc,
             product_product pp,
             product_template pt
        WHERE tld.test_line_id = tl.id
          AND tl.check_id = qc.id
          AND qc.product_id = pp.id
          AND pp.product_tmpl_id = pt.id
          AND tld.name = 'Muestra positiva'
          AND tld.evaluation_type = 'vama_multi_check'
          AND qc.state IN ('draft', 'in_progress')
          AND pt.default_code = ANY(%s)
    """, (MAPPING_POSITIVE, list(SPHM_CODES)))
    pos_det = cr.rowcount

    # Propagar a checks abiertos — negativa
    cr.execute("""
        UPDATE amunet_quality_test_line_detail tld
        SET text_phrase_mapping = %s, write_date = NOW()
        FROM amunet_quality_test_line tl,
             amunet_quality_check qc,
             product_product pp,
             product_template pt
        WHERE tld.test_line_id = tl.id
          AND tl.check_id = qc.id
          AND qc.product_id = pp.id
          AND pp.product_tmpl_id = pt.id
          AND tld.name = 'Muestra negativa'
          AND tld.evaluation_type = 'vama_multi_check'
          AND qc.state IN ('draft', 'in_progress')
          AND pt.default_code = ANY(%s)
    """, (MAPPING_NEGATIVE, list(SPHM_CODES)))
    neg_det = cr.rowcount

    _logger.info(
        "Migración 3.18.0 — #6/#7 → NO CUMPLE | spec_configs: pos=%d neg=%d | details: pos=%d neg=%d",
        pos_sc, neg_sc, pos_det, neg_det,
    )
