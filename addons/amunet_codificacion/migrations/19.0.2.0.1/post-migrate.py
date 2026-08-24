import logging
_logger = logging.getLogger(__name__)

EQUIPOS = ('AMU-83672', 'EQBAD01', 'EQCBV01', 'EQINC01', 'EQTER01', 'EQTER02', 'EQVOR01')


def migrate(cr, version):
    cr.execute("SELECT id FROM product_category WHERE complete_name = 'Distribucion / Equipo' LIMIT 1")
    row = cr.fetchone()
    if not row:
        _logger.warning("Categoría 'Distribucion / Equipo' no encontrada — migración omitida")
        return
    categ_id = row[0]
    placeholders = ','.join(['%s'] * len(EQUIPOS))
    cr.execute(
        f"UPDATE product_template SET categ_id = %s WHERE default_code IN ({placeholders})",
        (categ_id, *EQUIPOS),
    )
    _logger.info("Equipos actualizados a categoría 'Distribucion / Equipo': %d productos", cr.rowcount)
