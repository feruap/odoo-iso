import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migración 3.12.0: MAVI-07 limpiar Interpretación de Líneas; MAVI-09 rangos liberación/migración."""

    # ── MAVI-07: desactivar todos los 'Interpretación de Líneas' activos ──────
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET active = false, write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        WHERE sc.product_parameter_rel_id = r.id
          AND r.parameter_code = 'MAVI-07'
          AND sc.specification_name = 'Interpretación de Líneas'
          AND sc.active = true
    """)
    lineas_off = cr.rowcount
    _logger.info("MAVI-07 3.12.0: %d 'Interpretación de Líneas' desactivados", lineas_off)

    # ── MAVI-07: activar el más reciente 'Muestra positiva' por rel (STBs y similares) ──
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config
        SET active = true, evaluation_type = 'vama_multi_check', write_date = NOW()
        WHERE id IN (
            SELECT MAX(sc.id)
            FROM amunet_quality_parameter_specification_config sc
            JOIN amunet_quality_parameter_product_rel r ON r.id = sc.product_parameter_rel_id
            WHERE r.parameter_code = 'MAVI-07'
              AND sc.specification_name = 'Muestra positiva'
              AND sc.text_phrase_mapping LIKE '%%fixed_sample_type%%'
            GROUP BY sc.product_parameter_rel_id
        )
        AND active = false
    """)
    pos_on = cr.rowcount
    _logger.info("MAVI-07 3.12.0: %d 'Muestra positiva' activados", pos_on)

    # ── MAVI-07: activar el más reciente 'Muestra negativa' por rel ──────────
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config
        SET active = true, evaluation_type = 'vama_multi_check', write_date = NOW()
        WHERE id IN (
            SELECT MAX(sc.id)
            FROM amunet_quality_parameter_specification_config sc
            JOIN amunet_quality_parameter_product_rel r ON r.id = sc.product_parameter_rel_id
            WHERE r.parameter_code = 'MAVI-07'
              AND sc.specification_name = 'Muestra negativa'
              AND sc.text_phrase_mapping LIKE '%%fixed_sample_type%%'
            GROUP BY sc.product_parameter_rel_id
        )
        AND active = false
    """)
    neg_on = cr.rowcount
    _logger.info("MAVI-07 3.12.0: %d 'Muestra negativa' activados", neg_on)

    # Hojas maestras en alcance (productos terminados se abordan en migración posterior)
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

    # ── MAVI-09: Liberación de conjugado 0-0 → 1-30 (solo hojas maestras) ────
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET min_value = 1, max_value = 30, write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE sc.product_parameter_rel_id = r.id
          AND r.parameter_code = 'MAVI-09'
          AND pt.default_code = ANY(%s)
          AND sc.specification_name = 'Liberación de conjugado'
          AND sc.active = true
          AND sc.min_value = 0 AND sc.max_value = 0
    """, (list(SPHM_CODES),))
    lib_upd = cr.rowcount
    _logger.info("MAVI-09 3.12.0: %d 'Liberación de conjugado' → rango 1-30", lib_upd)

    # ── MAVI-09: Migración de conjugado 0-0 → 30-180 (solo hojas maestras) ───
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET min_value = 30, max_value = 180, write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE sc.product_parameter_rel_id = r.id
          AND r.parameter_code = 'MAVI-09'
          AND pt.default_code = ANY(%s)
          AND sc.specification_name = 'Migración de conjugado'
          AND sc.active = true
          AND sc.min_value = 0 AND sc.max_value = 0
    """, (list(SPHM_CODES),))
    mig_upd = cr.rowcount
    _logger.info("MAVI-09 3.12.0: %d 'Migración de conjugado' → rango 30-180", mig_upd)

    # ── MAVI-09: Tiempo de liberación 0-0 → 1-30 (solo hojas maestras) ───────
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET min_value = 1, max_value = 30, write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE sc.product_parameter_rel_id = r.id
          AND r.parameter_code = 'MAVI-09'
          AND pt.default_code = ANY(%s)
          AND sc.specification_name = 'Tiempo de liberación'
          AND sc.active = true
          AND sc.min_value = 0 AND sc.max_value = 0
    """, (list(SPHM_CODES),))
    tlib_upd = cr.rowcount
    _logger.info("MAVI-09 3.12.0: %d 'Tiempo de liberación' → rango 1-30", tlib_upd)

    # ── MAVI-09: Tiempo de migración 0-0 → 30-180 (solo hojas maestras) ──────
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET min_value = 30, max_value = 180, write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE sc.product_parameter_rel_id = r.id
          AND r.parameter_code = 'MAVI-09'
          AND pt.default_code = ANY(%s)
          AND sc.specification_name = 'Tiempo de migración'
          AND sc.active = true
          AND sc.min_value = 0 AND sc.max_value = 0
    """, (list(SPHM_CODES),))
    tmig_upd = cr.rowcount
    _logger.info("MAVI-09 3.12.0: %d 'Tiempo de migración' → rango 30-180", tmig_upd)

    # ── MAVI-09: Tiempo de migración en 4 cm de membrana 0-0 → 30-180 ────────
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET min_value = 30, max_value = 180, write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE sc.product_parameter_rel_id = r.id
          AND r.parameter_code = 'MAVI-09'
          AND pt.default_code = ANY(%s)
          AND sc.specification_name = 'Tiempo de migración en 4 cm de membrana.'
          AND sc.active = true
          AND sc.min_value = 0 AND sc.max_value = 0
    """, (list(SPHM_CODES),))
    tmem_upd = cr.rowcount
    _logger.info("MAVI-09 3.12.0: %d 'Tiempo de migración 4 cm membrana' → rango 30-180", tmem_upd)

    _logger.info(
        "Migración 3.12.0 completa — MAVI-07: %d Líneas off, %d Pos on, %d Neg on | "
        "MAVI-09: %d Lib.conj, %d Mig.conj, %d T.lib, %d T.mig, %d T.mig4cm",
        lineas_off, pos_on, neg_on, lib_upd, mig_upd, tlib_upd, tmig_upd, tmem_upd,
    )
