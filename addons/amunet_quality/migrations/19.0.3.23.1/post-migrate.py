import logging

_logger = logging.getLogger(__name__)

# parameter_id para MAVI-04 (el más usado, id=1) y MAVI-11 (id=64)
PARAM_MAVI_04 = 1
PARAM_MAVI_11 = 64

# specification_id apunta a amunet_quality_check_parameter_specification (spec base/template)
SPECS_MAVI_04 = [
    {
        'specification_name': 'Manchas y/o suciedad',
        'specification_id': 171,
        'evaluation_type': 'binary_selection',
        'sequence': 10,
        'binary_option_pass': 'Sin Manchas y/o suciedad',
        'binary_option_fail': 'Con Manchas y/o suciedad',
        'acceptance_criteria': 'Manchas y/o suciedad',
    },
    {
        'specification_name': 'Rasgaduras',
        'specification_id': 170,
        'evaluation_type': 'binary_selection',
        'sequence': 10,
        'binary_option_pass': 'Sin Rasgaduras',
        'binary_option_fail': 'Con Rasgaduras',
        'acceptance_criteria': 'Rasgaduras',
    },
    {
        'specification_name': 'Deformidad o deterioro.',
        'specification_id': 204,
        'evaluation_type': 'binary_selection',
        'sequence': 10,
        'binary_option_pass': 'Sin Deformidad o deterioro.',
        'binary_option_fail': 'Con Deformidad o deterioro.',
        'acceptance_criteria': 'Deformidad o deterioro.',
    },
]

SPEC_MAVI_11 = {
    'specification_name': 'Altura 6 u 8 cm (según aplique)',
    'specification_id': 414,
    'evaluation_type': 'mavi_11_height',
    'sequence': 10,
    'binary_option_pass': 'Seleccione',
    'binary_option_fail': 'Opción A: 6 cm.',
    'acceptance_criteria': 'Altura 6 u 8 cm (según aplique)',
}


def _ensure_mavi04_rel(cr, product_code):
    """Crea el rel MAVI-04 si no existe; devuelve el rel_id."""
    cr.execute("""
        SELECT r.id FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE pt.default_code = %s AND r.parameter_code = 'MAVI-04' AND r.active = true
        LIMIT 1
    """, (product_code,))
    row = cr.fetchone()
    if row:
        return row[0], False

    cr.execute("""
        INSERT INTO amunet_quality_parameter_product_rel
          (product_tmpl_id, parameter_id, parameter_code, sequence, active,
           create_uid, write_uid, create_date, write_date)
        SELECT pt.id, %s, 'MAVI-04', 10, true, 1, 1, NOW(), NOW()
        FROM product_template pt WHERE pt.default_code = %s
        RETURNING id
    """, (PARAM_MAVI_04, product_code))
    return cr.fetchone()[0], True


def _add_specs(cr, rel_id, specs):
    """Inserta specs en un rel solo si no existen ya (por nombre)."""
    inserted = 0
    for spec in specs:
        cr.execute("""
            SELECT 1 FROM amunet_quality_parameter_specification_config
            WHERE product_parameter_rel_id = %s
              AND specification_name = %s AND active = true
        """, (rel_id, spec['specification_name']))
        if cr.fetchone():
            continue
        cr.execute("""
            INSERT INTO amunet_quality_parameter_specification_config
              (product_parameter_rel_id, specification_id, specification_name,
               evaluation_type, sequence,
               binary_option_pass, binary_option_fail, acceptance_criteria,
               min_value, max_value, active,
               create_uid, write_uid, create_date, write_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, 0, true, 1, 1, NOW(), NOW())
        """, (
            rel_id,
            spec['specification_id'],
            spec['specification_name'],
            spec['evaluation_type'],
            spec['sequence'],
            spec['binary_option_pass'],
            spec['binary_option_fail'],
            spec['acceptance_criteria'],
        ))
        inserted += 1
    return inserted


def migrate(cr, version):
    """Migración 3.23.0: añade MAVI-04 (y MAVI-11 en SPHMC34) que faltaban.

    - SPHMC04 (Albúmina/competitiva): sin rel MAVI-04 → crea rel + 3 specs binarios.
    - SPHMC34 (CA 15-3): sin rel MAVI-04 + sin specs activos en MAVI-11 → idem + 1 spec de altura.
    """
    total_rels = 0
    total_specs = 0

    # ── SPHMC04: solo falta MAVI-04 ──────────────────────────────────────────
    rel_04, created = _ensure_mavi04_rel(cr, 'SPHMC04')
    if created:
        total_rels += 1
    total_specs += _add_specs(cr, rel_04, SPECS_MAVI_04)

    # ── SPHMC34: falta MAVI-04 y MAVI-11 specs ───────────────────────────────
    rel_34_04, created = _ensure_mavi04_rel(cr, 'SPHMC34')
    if created:
        total_rels += 1
    total_specs += _add_specs(cr, rel_34_04, SPECS_MAVI_04)

    # MAVI-11 para SPHMC34: rel ya existe (id=1633), solo faltan specs activos
    cr.execute("""
        SELECT r.id FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON pt.id = r.product_tmpl_id
        WHERE pt.default_code = 'SPHMC34' AND r.parameter_code = 'MAVI-11' AND r.active = true
        LIMIT 1
    """)
    row = cr.fetchone()
    if row:
        total_specs += _add_specs(cr, row[0], [SPEC_MAVI_11])
    else:
        cr.execute("""
            INSERT INTO amunet_quality_parameter_product_rel
              (product_tmpl_id, parameter_id, parameter_code, sequence, active,
               create_uid, write_uid, create_date, write_date)
            SELECT pt.id, %s, 'MAVI-11', 10, true, 1, 1, NOW(), NOW()
            FROM product_template pt WHERE pt.default_code = 'SPHMC34'
            RETURNING id
        """, (PARAM_MAVI_11,))
        new_rel = cr.fetchone()[0]
        total_rels += 1
        total_specs += _add_specs(cr, new_rel, [SPEC_MAVI_11])

    _logger.info(
        "Migración 3.23.0 — Parámetros faltantes: %d rels creados, %d specs insertados",
        total_rels, total_specs,
    )
