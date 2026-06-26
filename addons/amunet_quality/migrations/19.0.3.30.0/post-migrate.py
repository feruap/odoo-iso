import logging

_logger = logging.getLogger(__name__)

# ─── Parámetros base estables (seeded, mismos IDs en staging y producción) ────
VAMA063_ID  = 62   # VAMA-063 "Determinación de información"
MAVI04_ID   = 1    # MAVI-04  "Aspectos"
MAVI11_ID   = 64   # MAVI-11  "Longitud y/o grosor"

# Specs base de MAVI-11 (parameter_id=64)
SPEC_ANCHO = 379
SPEC_LARGO = 380
SPEC_ALTO  = 403

# Specs base de MAVI-04 (parameter_id=1) usados en cajas
MAVI04_SPECS = [
    (1,   'Polvo',                   'binary_selection',  'Sin polvo',                   'Con polvo'),
    (171, 'Manchas y/o suciedad',    'binary_selection',  'Sin manchas y/o suciedad',    'Con manchas y/o suciedad'),
    (170, 'Rasgaduras',              'binary_selection',  'Sin rasgaduras',               'Con rasgaduras'),
    (180, 'Letra',                   'binary_selection',  'Letra legible',                'Letra ilegible'),
    (175, 'Deformidad o deterioro',  'binary_selection',  'Sin deformidad o deterioro',   'Con deformidad o deterioro'),
]

# Dimensiones para las cajas estándar (MICAJ01-07, 10-14)
CAJAS_ESTANDAR = [
    'MICAJ01','MICAJ02','MICAJ03','MICAJ04','MICAJ05',
    'MICAJ06','MICAJ07','MICAJ10','MICAJ11','MICAJ12',
    'MICAJ13','MICAJ14',
]
DIM_ESTANDAR = {SPEC_ANCHO: (105, 110, 115), SPEC_LARGO: (195, 200, 205), SPEC_ALTO: (85, 90, 95)}

CAJAS_69 = ['MICAJ08', 'MICAJ09']
DIM_69   = {SPEC_ANCHO: (64, 69, 74), SPEC_LARGO: (64, 69, 74), SPEC_ALTO: (103, 108, 113)}

DIM_15   = {SPEC_ANCHO: (105, 110, 115), SPEC_LARGO: (131, 136, 141), SPEC_ALTO: (50, 55, 60)}


# ─── Nuevas cajas a crear ──────────────────────────────────────────────────────
MICAJ16 = {
    'code':     'MICAJ16',
    'qp_name':  'Caja Caple Antidoping Saliva',
    'dims':     {SPEC_ANCHO: (105, 110, 115), SPEC_LARGO: (195, 200, 205), SPEC_ALTO: (85, 90, 95)},
}
MICAJ19 = {
    'code':     'MICAJ19',
    'qp_name':  'Caja Caple HEMOGLINET 5 piezas',
    'dims':     {SPEC_ANCHO: (75, 80, 85), SPEC_LARGO: (125, 130, 135), SPEC_ALTO: (75, 80, 85)},
}
NUEVAS_CAJAS = [MICAJ16, MICAJ19]

ALL_MICAJ_CODES = CAJAS_ESTANDAR + CAJAS_69 + ['MICAJ15'] + [c['code'] for c in NUEVAS_CAJAS]


INSCC001_NAME = 'Revisión de información'


def _get_inscc001_id(cr):
    """Obtiene o crea el parámetro INSCC-001 y devuelve su id."""
    cr.execute("SELECT id FROM amunet_quality_check_parameter WHERE code='INSCC-001'")
    row = cr.fetchone()
    if row:
        inscc001_id = row[0]
        # Asegurar nombre correcto aunque ya existiera
        cr.execute("""
            UPDATE amunet_quality_check_parameter
            SET name=%s, write_date=NOW() WHERE id=%s AND name != %s
        """, (INSCC001_NAME, inscc001_id, INSCC001_NAME))
        return inscc001_id
    cr.execute("""
        INSERT INTO amunet_quality_check_parameter
            (name, code, active, create_uid, write_uid, create_date, write_date)
        VALUES
            (%s,'INSCC-001',true,1,1,NOW(),NOW())
        RETURNING id
    """, (INSCC001_NAME,))
    inscc001_id = cr.fetchone()[0]
    _logger.info("Migración 3.30.0 — Creado parámetro INSCC-001 id=%d", inscc001_id)

    # Crear las 3 especificaciones base
    base_specs = [
        ('Nombre (Cuando aplique).',             'binary_with_notes'),
        ('Contacto (Cuando aplique).',           'binary_with_notes'),
        ('Registro sanitario (Cuando aplique).', 'binary_with_notes'),
    ]
    for name, ev in base_specs:
        cr.execute("""
            INSERT INTO amunet_quality_check_parameter_specification
                (parameter_id, name, evaluation_type, create_uid, write_uid, create_date, write_date)
            VALUES (%s, %s, %s, 1, 1, NOW(), NOW())
        """, (inscc001_id, name, ev))
    _logger.info("Migración 3.30.0 — Creadas 3 specs base para INSCC-001")
    return inscc001_id


def _get_inscc001_spec_ids(cr, inscc001_id):
    """Devuelve (spec_id_nombre, spec_id_contacto, spec_id_registro)."""
    cr.execute("""
        SELECT id, name FROM amunet_quality_check_parameter_specification
        WHERE parameter_id=%s ORDER BY id
    """, (inscc001_id,))
    rows = {r[1]: r[0] for r in cr.fetchall()}
    return (
        rows.get('Nombre (Cuando aplique).'),
        rows.get('Contacto (Cuando aplique).'),
        rows.get('Registro sanitario (Cuando aplique).'),
    )


def _replace_vama063_with_inscc001(cr, inscc001_id):
    """Reemplaza VAMA-063 por INSCC-001 en QPs, rels y spec_configs."""

    # QPs que tienen VAMA-063 (antes de borrarlo)
    cr.execute("""
        SELECT amunet_quality_point_id
        FROM amunet_quality_check_parameter_amunet_quality_point_rel
        WHERE amunet_quality_check_parameter_id = %s
    """, (VAMA063_ID,))
    qp_ids = [r[0] for r in cr.fetchall()]

    if not qp_ids:
        _logger.info("Migración 3.30.0 — VAMA-063 ya no está en ningún QP, omitiendo reemplazo")
        return

    # Borrar VAMA-063 de esos QPs
    cr.execute("""
        DELETE FROM amunet_quality_check_parameter_amunet_quality_point_rel
        WHERE amunet_quality_check_parameter_id = %s
    """, (VAMA063_ID,))

    # Agregar INSCC-001 donde no esté ya
    for qp_id in qp_ids:
        cr.execute("""
            SELECT 1 FROM amunet_quality_check_parameter_amunet_quality_point_rel
            WHERE amunet_quality_check_parameter_id=%s AND amunet_quality_point_id=%s
        """, (inscc001_id, qp_id))
        if not cr.fetchone():
            cr.execute("""
                INSERT INTO amunet_quality_check_parameter_amunet_quality_point_rel
                    (amunet_quality_check_parameter_id, amunet_quality_point_id)
                VALUES (%s, %s)
            """, (inscc001_id, qp_id))

    # product_parameter_rels
    cr.execute("""
        UPDATE amunet_quality_parameter_product_rel
        SET parameter_id    = %s,
            parameter_code  = 'INSCC-001',
            parameter_name  = %s,
            display_name    = '[INSCC-001] ' || %s,
            write_date      = NOW()
        WHERE parameter_id = %s
    """, (inscc001_id, INSCC001_NAME, INSCC001_NAME, VAMA063_ID))
    rels_updated = cr.rowcount

    # spec_configs
    cr.execute("""
        UPDATE amunet_quality_parameter_specification_config
        SET parameter_id = %s, write_date = NOW()
        WHERE parameter_id = %s
    """, (inscc001_id, VAMA063_ID))
    configs_updated = cr.rowcount

    _logger.info(
        "Migración 3.30.0 — VAMA-063→INSCC-001: %d QPs, %d rels, %d spec_configs",
        len(qp_ids), rels_updated, configs_updated
    )


def _fix_dimensiones(cr, codigos, dims):
    """Actualiza min/nom/max para los spec_ids dados, en las cajas indicadas."""
    for spec_id, (mn, nom, mx) in dims.items():
        cr.execute("""
            UPDATE amunet_quality_parameter_specification_config sc
            SET min_value     = %s,
                nominal_value = %s,
                max_value     = %s,
                write_date    = NOW()
            WHERE sc.specification_id = %s
              AND sc.product_parameter_rel_id IN (
                  SELECT pr.id
                  FROM amunet_quality_parameter_product_rel pr
                  JOIN product_product pp ON pp.product_tmpl_id = pr.product_tmpl_id
                  WHERE pp.default_code = ANY(%s)
                    AND pr.parameter_id = %s
              )
        """, (mn, nom, mx, spec_id, list(codigos), MAVI11_ID))
    _logger.info("Migración 3.30.0 — Dimensiones actualizadas para %s", codigos)


def _get_picking_type_id(cr):
    """Devuelve el primer picking type de tipo incoming (Recepciones)."""
    cr.execute("SELECT id FROM stock_picking_type WHERE code='incoming' ORDER BY id LIMIT 1")
    row = cr.fetchone()
    return row[0] if row else 1


def _crear_qp_caja(cr, caja, inscc001_id, picking_type_id):
    """Crea un Quality Point completo para la nueva caja si no existe."""
    code = caja['code']
    cr.execute("SELECT id FROM product_product WHERE default_code=%s", (code,))
    pp_row = cr.fetchone()
    if not pp_row:
        _logger.warning("Migración 3.30.0 — Producto %s no encontrado, omitiendo", code)
        return None

    pp_id = pp_row[0]
    cr.execute("SELECT product_tmpl_id FROM product_product WHERE id=%s", (pp_id,))
    tmpl_id = cr.fetchone()[0]

    # ¿Ya existe un QP para este producto?
    cr.execute("""
        SELECT qp.id FROM amunet_quality_point qp
        JOIN amunet_quality_point_product_product_rel rel ON rel.amunet_quality_point_id=qp.id
        WHERE rel.product_product_id = %s
    """, (pp_id,))
    if cr.fetchone():
        _logger.info("Migración 3.30.0 — QP ya existe para %s, omitiendo", code)
        return None

    # Crear QP
    cr.execute("""
        INSERT INTO amunet_quality_point (name, active, company_id, create_uid, write_uid, create_date, write_date)
        VALUES (%s, true, 1, 1, 1, NOW(), NOW())
        RETURNING id
    """, (caja['qp_name'],))
    qp_id = cr.fetchone()[0]

    # Vincular producto
    cr.execute("""
        INSERT INTO amunet_quality_point_product_product_rel
            (amunet_quality_point_id, product_product_id)
        VALUES (%s, %s)
    """, (qp_id, pp_id))

    # Vincular picking type
    cr.execute("""
        INSERT INTO amunet_quality_point_stock_picking_type_rel
            (amunet_quality_point_id, stock_picking_type_id)
        VALUES (%s, %s)
    """, (qp_id, picking_type_id))

    # Vincular parámetros al QP
    for param_id in [MAVI04_ID, MAVI11_ID, inscc001_id]:
        cr.execute("""
            INSERT INTO amunet_quality_check_parameter_amunet_quality_point_rel
                (amunet_quality_check_parameter_id, amunet_quality_point_id)
            VALUES (%s, %s)
        """, (param_id, qp_id))

    # Crear product_parameter_rels
    params = [
        (MAVI04_ID,   'MAVI-04',   'Aspectos',                           '[MAVI-04] Aspectos'),
        (MAVI11_ID,   'MAVI-11',   'Longitud y/o grosor',                '[MAVI-11] Longitud y/o grosor'),
        (inscc001_id, 'INSCC-001', 'Determinación de información en caja', '[INSCC-001] Determinación de información en caja'),
    ]
    rel_ids = {}
    for param_id, pcode, pname, dname in params:
        cr.execute("""
            INSERT INTO amunet_quality_parameter_product_rel
                (product_tmpl_id, parameter_id, parameter_code, parameter_name, display_name,
                 active, active_spec_count, spec_summary, create_uid, write_uid, create_date, write_date)
            VALUES (%s, %s, %s, %s, %s, true, 0, '', 1, 1, NOW(), NOW())
            RETURNING id
        """, (tmpl_id, param_id, pcode, pname, dname))
        rel_ids[param_id] = cr.fetchone()[0]

    # spec_configs para MAVI-04
    mavi04_rel_id = rel_ids[MAVI04_ID]
    for spec_id, sname, ev, opt_pass, opt_fail in MAVI04_SPECS:
        cr.execute("""
            INSERT INTO amunet_quality_parameter_specification_config
                (product_parameter_rel_id, specification_id, parameter_id, product_tmpl_id,
                 specification_name, evaluation_type,
                 binary_option_pass, binary_option_fail,
                 create_uid, write_uid, create_date, write_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, 1, NOW(), NOW())
        """, (mavi04_rel_id, spec_id, MAVI04_ID, tmpl_id,
              sname, ev, opt_pass, opt_fail))

    # spec_configs para MAVI-11 (dimensiones)
    mavi11_rel_id = rel_ids[MAVI11_ID]
    dim_names = {SPEC_ANCHO: 'Ancho', SPEC_LARGO: 'Largo', SPEC_ALTO: 'Alto'}
    for spec_id, (mn, nom, mx) in caja['dims'].items():
        cr.execute("""
            INSERT INTO amunet_quality_parameter_specification_config
                (product_parameter_rel_id, specification_id, parameter_id, product_tmpl_id,
                 specification_name, evaluation_type,
                 min_value, nominal_value, max_value,
                 create_uid, write_uid, create_date, write_date)
            VALUES (%s, %s, %s, %s, %s, 'numeric_range', %s, %s, %s, 1, 1, NOW(), NOW())
        """, (mavi11_rel_id, spec_id, MAVI11_ID, tmpl_id,
              dim_names[spec_id], mn, nom, mx))

    # spec_configs para INSCC-001
    inscc_rel_id = rel_ids[inscc001_id]
    inscc_specs = _get_inscc001_spec_ids(cr, inscc001_id)
    inscc_names = [
        'Nombre (Cuando aplique).',
        'Contacto (Cuando aplique).',
        'Registro sanitario (Cuando aplique).',
    ]
    for spec_id, sname in zip(inscc_specs, inscc_names):
        if not spec_id:
            continue
        cr.execute("""
            INSERT INTO amunet_quality_parameter_specification_config
                (product_parameter_rel_id, specification_id, parameter_id, product_tmpl_id,
                 specification_name, evaluation_type,
                 binary_option_pass, binary_option_fail,
                 create_uid, write_uid, create_date, write_date)
            VALUES (%s, %s, %s, %s, %s, 'binary_with_notes',
                    'La información es completa y correcta.',
                    'La información es incompleta e incorrecta. (Cuadro de texto)',
                    1, 1, NOW(), NOW())
        """, (inscc_rel_id, spec_id, inscc001_id, tmpl_id, sname))

    _logger.info("Migración 3.30.0 — QP id=%d creado para %s", qp_id, code)
    return (qp_id, rel_ids)


def _poblar_bridge_table(cr):
    """Llena amunet_quality_point_rel_personalization_rel para todos los QPs de cajas."""
    for code in ALL_MICAJ_CODES:
        # Obtener QP id para este producto
        cr.execute("""
            SELECT DISTINCT qp.id
            FROM amunet_quality_point qp
            JOIN amunet_quality_point_product_product_rel rel ON rel.amunet_quality_point_id=qp.id
            JOIN product_product pp ON pp.id=rel.product_product_id
            WHERE pp.default_code = %s
        """, (code,))
        qp_row = cr.fetchone()
        if not qp_row:
            continue
        qp_id = qp_row[0]

        # Obtener todos los rels activos del producto
        cr.execute("""
            SELECT pr.id
            FROM amunet_quality_parameter_product_rel pr
            JOIN product_product pp ON pp.product_tmpl_id = pr.product_tmpl_id
            WHERE pp.default_code = %s AND pr.active = true
        """, (code,))
        rel_ids = [r[0] for r in cr.fetchall()]

        for rel_id in rel_ids:
            # Verificar si ya existe esta combinación
            cr.execute("""
                SELECT 1 FROM amunet_quality_point_rel_personalization_rel
                WHERE point_id=%s AND rel_id=%s
            """, (qp_id, rel_id))
            if not cr.fetchone():
                cr.execute("""
                    INSERT INTO amunet_quality_point_rel_personalization_rel (point_id, rel_id)
                    VALUES (%s, %s)
                """, (qp_id, rel_id))

    _logger.info("Migración 3.30.0 — Bridge table poblada para todas las cajas")


def migrate(cr, version):
    """Migración 3.30.0: INSCC-001 para Material Impreso (cajas).

    - Crea parámetro INSCC-001 'Determinación de información en caja'.
    - Reemplaza VAMA-063 por INSCC-001 en QPs, rels y spec_configs de cajas.
    - Corrige Ancho/Largo/Alto en spec_configs (Ancho=110±5, Largo=200±5, Alto=90±5).
    - Crea QPs nuevos para MICAJ16 y MICAJ19 con parámetros y especificaciones.
    - Puebla bridge table amunet_quality_point_rel_personalization_rel.
    """

    inscc001_id = _get_inscc001_id(cr)
    _replace_vama063_with_inscc001(cr, inscc001_id)

    # Corregir dimensiones en cajas existentes
    _fix_dimensiones(cr, CAJAS_ESTANDAR, DIM_ESTANDAR)
    _fix_dimensiones(cr, CAJAS_69,       DIM_69)
    _fix_dimensiones(cr, ['MICAJ15'],    DIM_15)

    # Crear nuevas cajas
    picking_type_id = _get_picking_type_id(cr)
    for caja in NUEVAS_CAJAS:
        _crear_qp_caja(cr, caja, inscc001_id, picking_type_id)

    # Poblar bridge table
    _poblar_bridge_table(cr)

    # Renombrar INSCC-001 al nombre correcto en product_parameter_rels (si venían de otra versión)
    cr.execute("""
        UPDATE amunet_quality_parameter_product_rel
        SET parameter_name = %s,
            display_name   = '[INSCC-001] ' || %s,
            write_date     = NOW()
        WHERE parameter_id = %s AND parameter_name != %s
    """, (INSCC001_NAME, INSCC001_NAME, inscc001_id, INSCC001_NAME))

    # Actualizar líneas de hojas de análisis en progreso que aún usen VAMA-063
    cr.execute("""
        UPDATE amunet_quality_test_line
        SET parameter_id = %s,
            name         = %s,
            code         = 'INSCC-001',
            write_date   = NOW()
        WHERE parameter_id = %s
          AND check_id IN (
              SELECT id FROM amunet_quality_check WHERE state = 'in_progress'
          )
    """, (inscc001_id, INSCC001_NAME, VAMA063_ID))
    lines_updated = cr.rowcount
    _logger.info("Migración 3.30.0 — %d líneas de hojas en progreso actualizadas a INSCC-001", lines_updated)

    _logger.info("Migración 3.30.0 completada")
