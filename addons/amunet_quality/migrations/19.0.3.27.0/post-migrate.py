import logging

_logger = logging.getLogger(__name__)

PARAM_ID_MAVI16 = 92  # amunet_quality_check_parameter.id para MAVI-16

# Concentraciones y sus specs
CONCENTRATIONS = [
    {
        'key': 'low',
        'name': 'Concentración Baja (T<R o T≠R)',
        'scenarios': [
            # (step1_conc, step2_1_ctrl, step2_2_comp, verdict, message, seq)
            ('any',  'no',  'irrelevant', 'fail',
             'Inválido: No hay visualización de la línea de control.', 1),
            ('low',  'yes', 't_neq_r',   'pass',
             'T ≠ R: No hay formación de una línea de color en la región T.', 2),
            ('low',  'yes', 't_lt_r',    'pass',
             'T < R: La intensidad de la línea de color en la región T es menos intensa que la línea de color en la región R.', 3),
            ('low',  'yes', 't_eq_r',    'fail',
             'Inconsistente: Se esperaba Baja, se observó Intermedia.', 4),
            ('low',  'yes', 't_gt_r',    'fail',
             'Inconsistente: Se esperaba Baja, se observó Alta.', 5),
        ],
    },
    {
        'key': 'medium',
        'name': 'Concentración Intermedia (T~R)',
        'scenarios': [
            ('any',    'no',  'irrelevant', 'fail',
             'Inválido: No hay visualización de la línea de control.', 1),
            ('medium', 'yes', 't_neq_r',   'fail',
             'Inconsistente: Se esperaba Intermedia, no hubo reacción en T.', 2),
            ('medium', 'yes', 't_lt_r',    'fail',
             'Inconsistente: Se esperaba Intermedia, se observó Baja.', 3),
            ('medium', 'yes', 't_eq_r',    'pass',
             'T ~ R: La intensidad de la línea de color en la región T es igual o similar en intensidad que la línea de color en la región R.', 4),
            ('medium', 'yes', 't_gt_r',    'fail',
             'Inconsistente: Se esperaba Intermedia, se observó Alta.', 5),
        ],
    },
    {
        'key': 'high',
        'name': 'Concentración Alta (T>R)',
        'scenarios': [
            ('any',  'no',  'irrelevant', 'fail',
             'Inválido: No hay visualización de la línea de control.', 1),
            ('high', 'yes', 't_neq_r',   'fail',
             'Inconsistente: Se esperaba Alta, no hubo reacción en T.', 2),
            ('high', 'yes', 't_lt_r',    'fail',
             'Inconsistente: Se esperaba Alta, se observó Baja.', 3),
            ('high', 'yes', 't_eq_r',    'fail',
             'Inconsistente: Se esperaba Alta, se observó Intermedia.', 4),
            ('high', 'yes', 't_gt_r',    'pass',
             'T > R: La intensidad de la línea de color en la región T es más intensa que la línea de color en la región R.', 5),
        ],
    },
]

PRODUCTS = ('SPHMC25', 'SPHMC38', 'SPHMC52')
OLD_SPEC_CONFIG_IDS = (72609, 72693, 72791)


def _get_or_create_base_spec(cr, name):
    """Devuelve el id de la base spec para este nombre; la crea si no existe."""
    cr.execute("""
        SELECT id FROM amunet_quality_check_parameter_specification
        WHERE name = %s AND evaluation_type = 'decision_matrix'
        LIMIT 1
    """, (name,))
    row = cr.fetchone()
    if row:
        return row[0]
    cr.execute("""
        INSERT INTO amunet_quality_check_parameter_specification
          (parameter_id, name, evaluation_type, active, create_uid, write_uid, create_date, write_date)
        VALUES (%s, %s, 'decision_matrix', true, 1, 1, NOW(), NOW())
        RETURNING id
    """, (PARAM_ID_MAVI16, name))
    return cr.fetchone()[0]


def _add_scenario(cr, spec_id, step1_conc, step2_1_ctrl, step2_2_comp, verdict, message, seq):
    """Inserta un escenario en la matriz de decisión si no existe."""
    cr.execute("""
        SELECT 1 FROM amunet_quality_parameter_decision_matrix
        WHERE specification_id = %s
          AND step1_concentration = %s
          AND step2_1_control_visible = %s
          AND (step2_2_comparison = %s OR (step2_2_comparison IS NULL AND %s IS NULL))
    """, (spec_id, step1_conc, step2_1_ctrl, step2_2_comp, step2_2_comp))
    if cr.fetchone():
        return 0
    cr.execute("""
        INSERT INTO amunet_quality_parameter_decision_matrix
          (specification_id, sequence, step1_concentration, step2_1_control_visible,
           step2_2_comparison, verdict, result_message, active,
           create_uid, write_uid, create_date, write_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, true, 1, 1, NOW(), NOW())
    """, (spec_id, seq, step1_conc, step2_1_ctrl, step2_2_comp, verdict, message))
    return 1


def _create_spec_config(cr, rel_id, spec_id, conc_key, spec_name, product_tmpl_id, parameter_id, seq):
    """Crea un spec_config para la concentración indicada si no existe."""
    cr.execute("""
        SELECT 1 FROM amunet_quality_parameter_specification_config
        WHERE product_parameter_rel_id = %s AND specification_id = %s AND active = true
    """, (rel_id, spec_id))
    if cr.fetchone():
        return 0
    cr.execute("""
        INSERT INTO amunet_quality_parameter_specification_config
          (product_parameter_rel_id, specification_id, specification_name,
           evaluation_type, acceptance_criteria, sequence,
           product_tmpl_id, parameter_id,
           active, create_uid, write_uid, create_date, write_date)
        VALUES (%s, %s, %s, 'decision_matrix', %s, %s, %s, %s,
                true, 1, 1, NOW(), NOW())
    """, (rel_id, spec_id, spec_name, conc_key, seq, product_tmpl_id, parameter_id))
    return 1


def migrate(cr, version):
    """Migración 3.27.0: implementa MAVI-15 con 3 recuadros por concentración.

    Para SPHMC25, SPHMC38 y SPHMC52:
      - Crea 3 base specs (Baja/Intermedia/Alta) con su matriz de decisión
      - Reemplaza el spec_config único por 3 (uno por concentración)
      - Renombra el rel MAVI-16 a 'Visualización de líneas semicuantitativas'
    """
    # 1. Crear los 3 base specs y sus escenarios
    spec_ids = {}
    total_scenarios = 0
    for conc in CONCENTRATIONS:
        spec_id = _get_or_create_base_spec(cr, conc['name'])
        spec_ids[conc['key']] = spec_id
        for scenario in conc['scenarios']:
            total_scenarios += _add_scenario(cr, spec_id, *scenario)
        _logger.info("Migración 3.27.0 — Base spec '%s' id=%d", conc['name'], spec_id)

    # 2. Procesar cada producto semicuantitativo
    total_configs = 0
    for product_code in PRODUCTS:
        # Obtener el rel MAVI-16 del producto
        cr.execute("""
            SELECT r.id, r.parameter_id, pt.id AS tmpl_id
            FROM amunet_quality_parameter_product_rel r
            JOIN product_template pt ON pt.id = r.product_tmpl_id
            WHERE pt.default_code = %s AND r.parameter_code = 'MAVI-16' AND r.active = true
            LIMIT 1
        """, (product_code,))
        row = cr.fetchone()
        if not row:
            _logger.warning("Migración 3.27.0 — No se encontró rel MAVI-16 para %s", product_code)
            continue

        rel_id, param_id, tmpl_id = row

        # Renombrar el rel a 'Visualización de líneas semicuantitativas'
        cr.execute("""
            UPDATE amunet_quality_parameter_product_rel
            SET parameter_name = 'Visualización de líneas semicuantitativas',
                display_name   = '[MAVI-15] Visualización de líneas semicuantitativas',
                write_date     = NOW()
            WHERE id = %s
              AND parameter_name != 'Visualización de líneas semicuantitativas'
        """, (rel_id,))

        # Desactivar el spec_config único actual
        cr.execute("""
            UPDATE amunet_quality_parameter_specification_config
            SET active = false, write_date = NOW()
            WHERE product_parameter_rel_id = %s
              AND specification_id = 207
              AND active = true
        """, (rel_id,))

        # Crear 3 nuevos spec_configs (uno por concentración)
        for seq, conc in enumerate(CONCENTRATIONS, start=10):
            total_configs += _create_spec_config(
                cr, rel_id, spec_ids[conc['key']],
                conc['key'], conc['name'],
                tmpl_id, param_id,
                seq * 10,
            )

    _logger.info(
        "Migración 3.27.0 — MAVI-15: %d escenarios creados, %d spec_configs creados",
        total_scenarios, total_configs,
    )
