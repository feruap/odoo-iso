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
    """Migración 3.14.0: MAVI-07 acceptance_criteria + limpiar specs de Visualización en MAVI-11."""

    # ── Desactivar specs de Visualización que se insertaron incorrectamente en MAVI-11 ──
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET active = false, write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        WHERE sc.product_parameter_rel_id = r.id
          AND r.parameter_code = 'MAVI-11'
          AND sc.specification_name = 'Visualización: Solo línea control (referencia #5)'
          AND sc.active = true
    """)
    mavi11_off = cr.rowcount
    _logger.info("3.14.0: %d specs 'Visualización' desactivados de MAVI-11 (ubicación incorrecta)", mavi11_off)

    # ── MAVI-07 Muestra negativa: acceptance_criteria ─────────────────────────────────
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET acceptance_criteria = 'Patrón #5 (Solo línea control, sin línea T)',
            write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE sc.product_parameter_rel_id = r.id
          AND r.parameter_code = 'MAVI-07'
          AND sc.specification_name = 'Muestra negativa'
          AND sc.active = true
          AND pt.default_code = ANY(%s)
    """, (list(SPHM_CODES),))
    neg_upd = cr.rowcount
    _logger.info("3.14.0: %d 'Muestra negativa' MAVI-07 — acceptance_criteria actualizado", neg_upd)

    # ── MAVI-07 Muestra positiva: acceptance_criteria ─────────────────────────────────
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET acceptance_criteria = 'Patrones #1-#4 (Línea T visible)',
            write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE sc.product_parameter_rel_id = r.id
          AND r.parameter_code = 'MAVI-07'
          AND sc.specification_name = 'Muestra positiva'
          AND sc.active = true
          AND pt.default_code = ANY(%s)
    """, (list(SPHM_CODES),))
    pos_upd = cr.rowcount
    _logger.info("3.14.0: %d 'Muestra positiva' MAVI-07 — acceptance_criteria actualizado", pos_upd)

    _logger.info(
        "Migración 3.14.0 completa — MAVI-11 off: %d | MAVI-07 neg: %d pos: %d",
        mavi11_off, neg_upd, pos_upd,
    )
