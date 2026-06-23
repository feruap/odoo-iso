import logging

_logger = logging.getLogger(__name__)

# IDs de base-parameter en amunet_quality_check_parameter
PARAM_ID_SEMICUANT = 92   # actualmente code='MAVI-16' — debe ser MAVI-15
PARAM_ID_COLORIM   = 123  # actualmente code='MAVI-16' — queda como MAVI-16 colorimétrico

PRODUCTS_SEMICUANT = ('SPHMC25', 'SPHMC38', 'SPHMC52')


def migrate(cr, version):
    """Migración 3.28.0: separa MAVI-15 (semicuantitativo) de MAVI-16 (colorimétrico).

    El parámetro base ID=92 era MAVI-16 pero solo lo usan SPHMC25/38/52
    (semicuantitativas). Se le cambia el código a MAVI-15 y el nombre
    a 'Visualización de líneas semicuantitativas'.

    El parámetro base ID=123 (MAVI-16) se renombra a 'Apariencia colorimétrica'
    para que coincida con las hojas que sí lo usan (SPHMC07, 09, 16, 26, etc.).

    También se actualizan los rels y spec_configs de las hojas semicuantitativas.
    """

    # 1. Renombrar base-parameter 92 → MAVI-15
    cr.execute("""
        UPDATE amunet_quality_check_parameter
        SET code       = 'MAVI-15',
            name       = 'Visualización de líneas semicuantitativas',
            write_date = NOW()
        WHERE id = %s AND code != 'MAVI-15'
    """, (PARAM_ID_SEMICUANT,))
    _logger.info("Migración 3.28.0 — Parámetro base %d renombrado a MAVI-15", PARAM_ID_SEMICUANT)

    # 2. Renombrar base-parameter 123 → nombre correcto para colorimétrico
    cr.execute("""
        UPDATE amunet_quality_check_parameter
        SET name       = 'Apariencia colorimétrica',
            write_date = NOW()
        WHERE id = %s AND name != 'Apariencia colorimétrica'
    """, (PARAM_ID_COLORIM,))
    _logger.info("Migración 3.28.0 — Parámetro base %d renombrado a Apariencia colorimétrica", PARAM_ID_COLORIM)

    # 3. Actualizar rels de SPHMC25/38/52: code → MAVI-15
    cr.execute("""
        UPDATE amunet_quality_parameter_product_rel r
        SET parameter_code = 'MAVI-15',
            parameter_name = 'Visualización de líneas semicuantitativas',
            display_name   = '[MAVI-15] Visualización de líneas semicuantitativas',
            write_date     = NOW()
        FROM product_template pt
        WHERE r.product_tmpl_id = pt.id
          AND pt.default_code   = ANY(%s)
          AND r.parameter_id    = %s
          AND r.active          = true
    """, (list(PRODUCTS_SEMICUANT), PARAM_ID_SEMICUANT))
    rels = cr.rowcount
    _logger.info("Migración 3.28.0 — %d rels actualizados a MAVI-15", rels)

    # 4. Actualizar spec_configs activos de SPHMC25/38/52 vinculados al parámetro
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config sc
        SET parameter_id = %s,
            write_date   = NOW()
        FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE sc.product_parameter_rel_id = r.id
          AND pt.default_code = ANY(%s)
          AND r.parameter_id  = %s
          AND sc.active       = true
          AND sc.parameter_id != %s
    """, (PARAM_ID_SEMICUANT, list(PRODUCTS_SEMICUANT), PARAM_ID_SEMICUANT, PARAM_ID_SEMICUANT))
    _logger.info("Migración 3.28.0 — spec_configs de semicuantitativas verificados")
