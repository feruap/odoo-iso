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

    # ── MAVI-09: Liberación de conjugado 0-0 → 1-30 ──────────────────────────
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET min_value = 1, max_value = 30, write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        WHERE sc.product_parameter_rel_id = r.id
          AND r.parameter_code = 'MAVI-09'
          AND sc.specification_name = 'Liberación de conjugado'
          AND sc.active = true
          AND sc.min_value = 0 AND sc.max_value = 0
    """)
    lib_upd = cr.rowcount
    _logger.info("MAVI-09 3.12.0: %d 'Liberación de conjugado' → rango 1-30", lib_upd)

    # ── MAVI-09: Migración de conjugado 0-0 → 30-180 ─────────────────────────
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET min_value = 30, max_value = 180, write_date = NOW()
        FROM amunet_quality_parameter_product_rel r
        WHERE sc.product_parameter_rel_id = r.id
          AND r.parameter_code = 'MAVI-09'
          AND sc.specification_name = 'Migración de conjugado'
          AND sc.active = true
          AND sc.min_value = 0 AND sc.max_value = 0
    """)
    mig_upd = cr.rowcount
    _logger.info("MAVI-09 3.12.0: %d 'Migración de conjugado' → rango 30-180", mig_upd)

    _logger.info(
        "Migración 3.12.0 completa — MAVI-07: %d Líneas off, %d Pos on, %d Neg on | "
        "MAVI-09: %d Liberación, %d Migración",
        lineas_off, pos_on, neg_on, lib_upd, mig_upd,
    )
