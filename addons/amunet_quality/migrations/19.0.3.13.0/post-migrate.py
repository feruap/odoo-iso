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
    """Migración 3.13.0: MAVI-11 — agregar spec Visualización: Solo línea control para todas las hojas maestras."""

    cr.execute("""
        SELECT id FROM amunet_quality_check_parameter_specification
        WHERE name ILIKE '%Visualización sólo de la línea control%'
        ORDER BY id LIMIT 1
    """)
    row = cr.fetchone()
    if not row:
        cr.execute("""
            SELECT id FROM amunet_quality_check_parameter_specification
            WHERE name ILIKE '%Visualización%'
            ORDER BY id LIMIT 1
        """)
        row = cr.fetchone()
    spec_master_id = row[0] if row else None

    if not spec_master_id:
        _logger.warning("MAVI-11 3.13.0: no se encontró spec master para Visualización; abortando insert.")
        return

    cr.execute("""
        INSERT INTO amunet_quality_parameter_specification_config
            (product_parameter_rel_id, specification_id, specification_name,
             evaluation_type, sequence, active,
             acceptance_criteria, binary_option_pass, binary_option_fail,
             create_date, write_date, create_uid, write_uid)
        SELECT
            r.id,
            %s,
            'Visualización: Solo línea control (referencia #5)',
            'binary_selection',
            20,
            true,
            'Solo línea control visible (referencia #5)',
            'Solo línea control visible (referencia #5) - CUMPLE',
            'Línea T visible u otro patrón - NO CUMPLE',
            NOW(), NOW(), 1, 1
        FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE r.parameter_code = 'MAVI-11'
          AND pt.default_code = ANY(%s)
          AND NOT EXISTS (
              SELECT 1 FROM amunet_quality_parameter_specification_config sc2
              WHERE sc2.product_parameter_rel_id = r.id
                AND sc2.specification_name = 'Visualización: Solo línea control (referencia #5)'
          )
    """, (spec_master_id, list(SPHM_CODES)))
    inserted = cr.rowcount
    _logger.info(
        "MAVI-11 3.13.0: %d specs 'Visualización: Solo línea control (referencia #5)' insertados",
        inserted,
    )
