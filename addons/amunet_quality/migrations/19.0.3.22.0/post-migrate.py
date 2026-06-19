import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migración 3.22.0: activa bloqueo de longitud de hoja en todas las SPHM.

    Habilita require_additional_info y crea las dos configs requeridas
    (Promedio de largo + Coeficiente de variación) en todos los productos
    con código SPHM*. Idempotente: no duplica configs existentes.
    """
    # 1. Activar require_additional_info en todas las SPHM
    cr.execute("""
        UPDATE product_template
        SET require_additional_info = true, write_date = NOW()
        WHERE default_code LIKE 'SPHM%%'
          AND (require_additional_info IS NOT TRUE)
    """)
    updated = cr.rowcount

    # 2. Obtener IDs de los dos campos de info adicional
    cr.execute("""
        SELECT id, name->>'en_US' as nombre
        FROM amunet_quality_additional_info_field
        WHERE id IN (1, 2)
        ORDER BY id
    """)
    fields = cr.fetchall()
    if len(fields) < 2:
        _logger.warning("Migración 3.22.0: no se encontraron los campos 1 y 2 de info adicional")
        return

    # 3. Insertar configs faltantes (idempotente con NOT EXISTS)
    cr.execute("""
        INSERT INTO amunet_quality_additional_info_config
          (product_tmpl_id, field_id, required, active, sequence,
           create_uid, write_uid, create_date, write_date)
        SELECT pt.id, f.field_id, true, true, f.seq, 1, 1, NOW(), NOW()
        FROM product_template pt
        CROSS JOIN (VALUES (1, 1), (2, 2)) AS f(field_id, seq)
        WHERE pt.default_code LIKE 'SPHM%%'
          AND NOT EXISTS (
            SELECT 1 FROM amunet_quality_additional_info_config aic
            WHERE aic.product_tmpl_id = pt.id AND aic.field_id = f.field_id
          )
    """)
    inserted = cr.rowcount

    # Contar total configuradas
    cr.execute("""
        SELECT COUNT(DISTINCT pt.id)
        FROM product_template pt
        WHERE pt.default_code LIKE 'SPHM%%'
          AND pt.require_additional_info = true
          AND (SELECT COUNT(*) FROM amunet_quality_additional_info_config aic
               WHERE aic.product_tmpl_id = pt.id) >= 2
    """)
    total = cr.fetchone()[0]

    _logger.info(
        "Migración 3.22.0 — Bloqueo longitud hoja: %d productos actualizados, "
        "%d configs insertadas, %d hojas SPHM con config completa",
        updated, inserted, total,
    )
