# -*- coding: utf-8 -*-
"""
Limpia SPHMC80 (Hoja Maestra ToRCH Herpes 1/2 IgG/IgM):
acumuló 132 specs activas de muchos productos distintos.
Deja solo las 8 correctas, idénticas a SPHMC01.
"""

KEEP_SPECS = [
    ('MAVI-04', 'Manchas y/o suciedad',             'binary_selection'),
    ('MAVI-04', 'Rasgaduras',                        'binary_selection'),
    ('MAVI-04', 'Deformidad o deterioro.',           'binary_selection'),
    ('MAVI-07', 'Muestra negativa',                  'vama_multi_check'),
    ('MAVI-07', 'Muestra positiva',                  'vama_multi_check'),
    ('MAVI-09', 'Tiempo de liberación',              'numeric_range'),
    ('MAVI-09', 'Tiempo de migración',               'numeric_range'),
    ('MAVI-11', 'Altura 6 u 8 cm (según aplique)',  'conditional_numeric_range'),
]


def migrate(cr, version):
    # 1. Obtener los rel_ids de SPHMC80
    cr.execute("""
        SELECT p.code, r.id
        FROM amunet_quality_parameter_product_rel r
        JOIN amunet_quality_check_parameter p ON p.id = r.parameter_id
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE pt.default_code = 'SPHMC80'
    """)
    rel_ids = {row[0]: row[1] for row in cr.fetchall()}
    if not rel_ids:
        return  # SPHMC80 no existe en esta BD, no hacer nada

    all_rel_ids = list(rel_ids.values())
    placeholders = ','.join(['%s'] * len(all_rel_ids))

    # 2. Desactivar TODOS los specs de esos rel_ids directamente
    cr.execute(f"""
        UPDATE amunet_quality_parameter_specification_config
        SET active = false, write_date = NOW()
        WHERE product_parameter_rel_id IN ({placeholders})
    """, all_rel_ids)

    # 3. Para cada spec correcta: reactivar el de menor id (incluyendo inactivos)
    for param_code, spec_name, eval_type in KEEP_SPECS:
        rel_id = rel_ids.get(param_code)
        if not rel_id:
            continue
        cr.execute("""
            UPDATE amunet_quality_parameter_specification_config
            SET active = true, write_date = NOW()
            WHERE id = (
                SELECT MIN(id)
                FROM amunet_quality_parameter_specification_config
                WHERE product_parameter_rel_id = %s
                  AND specification_name = %s
                  AND evaluation_type = %s
            )
        """, (rel_id, spec_name, eval_type))

    # 4. Log informativo (sin raise para no hacer rollback)
    cr.execute(f"""
        SELECT COUNT(*)
        FROM amunet_quality_parameter_specification_config
        WHERE product_parameter_rel_id IN ({placeholders}) AND active = true
    """, all_rel_ids)
    count = cr.fetchone()[0]
    import logging
    _logger = logging.getLogger(__name__)
    _logger.info("SPHMC80 limpieza: %d specs activas al final (esperadas 8)", count)
