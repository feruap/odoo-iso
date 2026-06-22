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


def migrate(cr, version):
    """Migración 3.17.0: sincronizar text_phrase_mapping del spec_config actual a todos
    los detalles MAVI-07 de checks abiertos (draft/in_progress) que aún tienen el
    formato antiguo (sin fixed_sample_type).

    También limpia multi_check_results_json con valores del formato viejo para que
    el analista los registre de nuevo con la nueva interfaz de 7 patrones.
    """
    # Sincronizar text_phrase_mapping desde spec_config hacia details con formato viejo
    # Nota: PostgreSQL no permite referenciar la tabla destino (tld) dentro de un JOIN
    # en la cláusula FROM; se usa sintaxis de coma para evitar ese error.
    cr.execute("""
        UPDATE amunet_quality_test_line_detail tld
        SET text_phrase_mapping = sc.text_phrase_mapping,
            acceptance_criteria = sc.acceptance_criteria,
            multi_check_results_json = NULL,
            write_date = NOW()
        FROM amunet_quality_parameter_specification_config sc,
             amunet_quality_test_line tl,
             amunet_quality_check qc,
             product_product pp,
             product_template pt
        WHERE tld.specification_config_id = sc.id
          AND tld.test_line_id = tl.id
          AND tl.check_id = qc.id
          AND qc.product_id = pp.id
          AND pp.product_tmpl_id = pt.id
          AND tld.evaluation_type = 'vama_multi_check'
          AND (tld.text_phrase_mapping NOT LIKE '%%fixed_sample_type%%'
               OR tld.text_phrase_mapping IS NULL)
          AND qc.state IN ('draft', 'in_progress')
          AND sc.active = true
          AND pt.default_code = ANY(%s)
    """, (list(SPHM_CODES),))
    updated = cr.rowcount

    _logger.info(
        "Migración 3.17.0 completa — %d detalles MAVI-07 sincronizados con nuevo mapeo (7 patrones)",
        updated,
    )
