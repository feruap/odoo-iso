import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migración 3.26.0: renombra MAVI-16 a 'Apariencia colorimétrica' en hojas SPHM.

    Actualiza parameter_name y display_name en los rels, y el nombre en los
    test lines de checks abiertos, para todos los productos SPHM%.
    """
    cr.execute("""
        UPDATE amunet_quality_parameter_product_rel r
        SET parameter_name = 'Apariencia colorimétrica',
            display_name   = '[MAVI-16] Apariencia colorimétrica',
            write_date     = NOW()
        FROM product_template pt
        WHERE r.product_tmpl_id = pt.id
          AND r.parameter_code  = 'MAVI-16'
          AND r.active          = true
          AND pt.default_code LIKE 'SPHM%%'
          AND r.parameter_name != 'Apariencia colorimétrica'
    """)
    rels = cr.rowcount

    cr.execute("""
        UPDATE amunet_quality_test_line tl
        SET name       = 'Apariencia colorimétrica',
            write_date = NOW()
        FROM amunet_quality_check qc
        JOIN product_product  pp ON pp.id = qc.product_id
        JOIN product_template pt ON pt.id = pp.product_tmpl_id
        WHERE tl.check_id  = qc.id
          AND tl.code       = 'MAVI-16'
          AND qc.state     IN ('draft', 'in_progress')
          AND pt.default_code LIKE 'SPHM%%'
          AND tl.name      != 'Apariencia colorimétrica'
    """)
    lines = cr.rowcount

    _logger.info(
        "Migración 3.26.0 — MAVI-16 renombrado a 'Apariencia colorimétrica': "
        "%d rels, %d test lines actualizados",
        rels, lines,
    )
