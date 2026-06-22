import logging

_logger = logging.getLogger(__name__)

SPHMC18_19 = ('SPHMC18', 'SPHMC19')


def migrate(cr, version):
    """Migración 3.19.0: MAVI-09 Tiempo de migración en SPHMC18 y SPHMC19 — rango 30-240.
    Estas pruebas demoran más que las inmunocromatográficas estándar.
    """
    # Actualizar spec_configs
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET max_value = 240, write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE sc.product_parameter_rel_id = r.id
          AND r.parameter_code = 'MAVI-09'
          AND sc.specification_name = 'Tiempo de migración'
          AND sc.active = true
          AND pt.default_code = ANY(%s)
    """, (list(SPHMC18_19),))
    sc_updated = cr.rowcount

    # Propagar a detalles en checks abiertos
    cr.execute("""
        UPDATE amunet_quality_test_line_detail tld
        SET max_value = 240, write_date = NOW()
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
          AND r.parameter_code = 'MAVI-09'
          AND tld.name = 'Tiempo de migración'
          AND qc.state IN ('draft', 'in_progress')
          AND pt.default_code = ANY(%s)
    """, (list(SPHMC18_19),))
    det_updated = cr.rowcount

    _logger.info(
        "Migración 3.19.0 — MAVI-09 SPHMC18/19 max 30→240: spec_configs=%d, detalles=%d",
        sc_updated, det_updated,
    )
