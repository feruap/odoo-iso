# -*- coding: utf-8 -*-
"""
STREX01 y STREX02: desactiva la spec mavi_07 "Interpretación de resultados"
que coexistía con las specs correctas vama_multi_check (Muestra negativa/positiva).
Las specs vama_multi_check ya estaban activas y con JSON correcto.
"""


def migrate(cr, version):
    import logging
    _logger = logging.getLogger(__name__)

    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET active = false, write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        JOIN amunet_quality_check_parameter p ON p.id = r.parameter_id
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE sc.product_parameter_rel_id = r.id
          AND p.code = 'MAVI-07'
          AND sc.evaluation_type = 'mavi_07'
          AND sc.active = true
          AND pt.default_code IN ('STREX01', 'STREX02')
    """)
    _logger.info("STREX01/STREX02: %d specs mavi_07 desactivadas", cr.rowcount)
