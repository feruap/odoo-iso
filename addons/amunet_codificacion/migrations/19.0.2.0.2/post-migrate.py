import logging
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        UPDATE ir_sequence irs
        SET prefix = 'C' || prefix
        FROM product_template pt
        WHERE pt.lot_sequence_id = irs.id
          AND pt.default_code LIKE 'SPCPL%%'
          AND irs.prefix NOT LIKE 'CPL%%'
    """)
    _logger.info("Prefijos de controles positivos corregidos a CPL: %d secuencias", cr.rowcount)
