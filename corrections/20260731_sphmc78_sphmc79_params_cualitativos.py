"""
Configura los parámetros de control de calidad para:
  SPHMC78 — Hoja Maestra HPV E7
  SPHMC79 — Hoja Maestra CARBA 5en1

Estructura cualitativa igual a Dengue IgG/IgM (SPHMC18):
  MAVI-09 × 2 — Tiempo de liberación (1–30 s) + Tiempo de migración (30–240 s)
  MAVI-07 × 2 — Muestra positiva + Muestra negativa (mavi_07_ternary)
  OLD-118 × 5 — Apariencia del empaque  (inspección visual, binaria)
  MAVI-11 × 3 — Longitud y/o grosor    (0-0 por confirmar con CERST)
  OLD-119 × 5 — Estructura del hisopo  (inspección visual, binaria)
  MAVI-04 × 5 — Aspectos               (inspección visual, binaria)

Idempotente: seguro de correr más de una vez.
Correr UNA VEZ después del deploy a producción.

NOTA: Los rangos de MAVI-09 y criterios de MAVI-07 están tomados de Dengue IgG/IgM
(SPHMC18) como referencia. Verificar contra el CERST de cada producto antes de activar
en producción definitiva.
"""
env = env  # noqa: F821 — Odoo shell

Product  = env['product.product']
Param    = env['amunet.quality.check.parameter']
ParamRel = env['amunet.quality.parameter.product.rel']
SpecCfg  = env['amunet.quality.parameter.specification.config']

PRODUCTOS = ['SPHMC78', 'SPHMC79']

# IDs de parámetros maestros
PARAM_MAVI09 = 69
PARAM_MAVI07 = 65
PARAM_OLD118 = 118
PARAM_MAVI11 = 64
PARAM_OLD119 = 119
PARAM_MAVI04 = 1

# ── Paso 1: Crear ParamRels ────────────────────────────────────────────────────
for code in PRODUCTOS:
    product = Product.search([('default_code', '=', code), ('active', '=', True)], limit=1)
    if not product:
        print(f"ERROR: producto {code} no encontrado — verifica que existe en esta BD")
        raise SystemExit(1)

    tmpl_id = product.product_tmpl_id.id
    print(f"\n{code} (tmpl_id={tmpl_id})")

    for param_id in [PARAM_MAVI09, PARAM_MAVI07, PARAM_OLD118, PARAM_MAVI11, PARAM_OLD119, PARAM_MAVI04]:
        param = Param.browse(param_id)
        exists = ParamRel.search([
            ('product_tmpl_id', '=', tmpl_id),
            ('parameter_id', '=', param_id),
        ], limit=1)
        if not exists:
            ParamRel.create({
                'product_tmpl_id': tmpl_id,
                'parameter_id':    param_id,
                'parameter_code':  param.code,
                'parameter_name':  param.name,
            })
            print(f"  ParamRel creado: {param.code}")
        else:
            print(f"  ParamRel ya existe (id={exists.id}): {param.code}")

env.cr.execute("SELECT id FROM pg_class WHERE relname='odoo_module_dependency' LIMIT 1")
env.cr.commit()  # flush para que SQL vea los nuevos rels

# ── Paso 2: Limpiar y fijar specs con SQL ─────────────────────────────────────
# Al crear el ParamRel, Odoo auto-copia todos los specs del master → duplicados.
# Limpiamos todo y dejamos solo las specs correctas para cada parámetro.

for code in PRODUCTOS:
    env.cr.execute("""
        SELECT rel.id, rel.parameter_id
        FROM amunet_quality_parameter_product_rel rel
        JOIN product_template pt ON pt.id = rel.product_tmpl_id
        JOIN product_product pp ON pp.product_tmpl_id = pt.id
        WHERE pp.default_code = %s
          AND rel.parameter_id IN (65, 69, 118, 64, 119, 1)
        ORDER BY rel.parameter_id
    """, (code,))
    rels = {row[1]: row[0] for row in env.cr.fetchall()}
    print(f"\n{code} rels: {rels}")

    rel09  = rels.get(PARAM_MAVI09)
    rel07  = rels.get(PARAM_MAVI07)
    rel118 = rels.get(PARAM_OLD118)
    rel11  = rels.get(PARAM_MAVI11)
    rel119 = rels.get(PARAM_OLD119)
    rel04  = rels.get(PARAM_MAVI04)

    # ── MAVI-09: borrar todos y recrear los 2 correctos ─────────────────────
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config WHERE product_parameter_rel_id=%s",
        (rel09,)
    )
    print(f"  MAVI-09: {env.cr.rowcount} specs borradas → recreando 2 correctas")
    env.cr.execute("""
        INSERT INTO amunet_quality_parameter_specification_config
          (product_parameter_rel_id, specification_id, specification_name,
           evaluation_type, min_value, max_value, acceptance_criteria, sequence,
           create_date, write_date, create_uid, write_uid)
        VALUES
          (%s, 146, 'Tiempo de liberación', 'numeric_range', 1, 30,
           '1 a 30 segundos', 10, NOW(), NOW(), 1, 1),
          (%s, 126, 'Tiempo de migración',  'numeric_range', 30, 240,
           '30 a 240 segundos', 20, NOW(), NOW(), 1, 1)
    """, (rel09, rel09))

    # ── MAVI-07: borrar todos y recrear los 2 correctos ─────────────────────
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config WHERE product_parameter_rel_id=%s",
        (rel07,)
    )
    print(f"  MAVI-07: {env.cr.rowcount} specs borradas → recreando 2 correctas")
    env.cr.execute("""
        INSERT INTO amunet_quality_parameter_specification_config
          (product_parameter_rel_id, specification_id, specification_name,
           evaluation_type, min_value, max_value, acceptance_criteria, sequence,
           create_date, write_date, create_uid, write_uid)
        VALUES
          (%s, 629, 'Muestra positiva', 'mavi_07_ternary', 0, 0,
           'Visualización sólo de la línea control patrón #5', 1, NOW(), NOW(), 1, 1),
          (%s, 628, 'Muestra negativa', 'mavi_07_ternary', 0, 0,
           'Visualización de la línea control y de la línea de prueba dentro del patrón #4 al #1',
           2, NOW(), NOW(), 1, 1)
    """, (rel07, rel07))

    # ── OLD-118: borrar todos y recrear 5 specs de inspección ───────────────
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config WHERE product_parameter_rel_id=%s",
        (rel118,)
    )
    print(f"  OLD-118: {env.cr.rowcount} specs borradas → recreando 5 de inspección")
    for seq, name in enumerate([
        '1.- Polvo', '2.- Manchas y/o suciedad', '3.- Rasgaduras',
        '5.- Deformidad o deterioro', '6.- Sellado',
    ], start=1):
        env.cr.execute("""
            INSERT INTO amunet_quality_parameter_specification_config
              (product_parameter_rel_id, specification_id, specification_name,
               evaluation_type, min_value, max_value, acceptance_criteria, sequence,
               create_date, write_date, create_uid, write_uid)
            VALUES (%s, 358, %s, 'binary_selection', 0, 0, %s, %s, NOW(), NOW(), 1, 1)
        """, (rel118, name, f'{name}: Conforme', seq * 10))

    # ── MAVI-11: borrar todos y recrear 3 dimensiones ───────────────────────
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config WHERE product_parameter_rel_id=%s",
        (rel11,)
    )
    print(f"  MAVI-11: {env.cr.rowcount} specs borradas → recreando 3 dimensiones")
    for seq, name in enumerate(['Ancho', 'Largo', 'Grosor'], start=1):
        env.cr.execute("""
            INSERT INTO amunet_quality_parameter_specification_config
              (product_parameter_rel_id, specification_id, specification_name,
               evaluation_type, min_value, max_value, acceptance_criteria, sequence,
               create_date, write_date, create_uid, write_uid)
            VALUES (%s, 370, %s, 'numeric_range', 0, 0, 'Según CERST', %s, NOW(), NOW(), 1, 1)
        """, (rel11, name, seq * 10))

    # ── OLD-119: borrar todos y recrear 5 specs ──────────────────────────────
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config WHERE product_parameter_rel_id=%s",
        (rel119,)
    )
    print(f"  OLD-119: {env.cr.rowcount} specs borradas → recreando 5 de inspección")
    for seq, name in enumerate([
        '1.- Polvo', '2.- Manchas y/o suciedad', '3.- Rasgaduras',
        '5.- Deformidad o deterioro', '6.- Sellado',
    ], start=1):
        env.cr.execute("""
            INSERT INTO amunet_quality_parameter_specification_config
              (product_parameter_rel_id, specification_id, specification_name,
               evaluation_type, min_value, max_value, acceptance_criteria, sequence,
               create_date, write_date, create_uid, write_uid)
            VALUES (%s, 363, %s, 'binary_selection', 0, 0, %s, %s, NOW(), NOW(), 1, 1)
        """, (rel119, name, f'{name}: Conforme', seq * 10))

    # ── MAVI-04: borrar todos y recrear 5 aspectos visuales ─────────────────
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config WHERE product_parameter_rel_id=%s",
        (rel04,)
    )
    print(f"  MAVI-04: {env.cr.rowcount} specs borradas → recreando 5 aspectos")
    aspectos = [
        (1,   'Polvo',                  'Sin polvo'),
        (171, 'Manchas y/o suciedad',   'Sin manchas ni suciedad'),
        (170, 'Rasgaduras',             'Sin rasgaduras'),
        (175, 'Deformidad o deterioro', 'Sin deformidad'),
        (190, 'Sellado',                'Sellado íntegro'),
    ]
    for seq, (spec_id, name, criteria) in enumerate(aspectos, start=1):
        env.cr.execute("""
            INSERT INTO amunet_quality_parameter_specification_config
              (product_parameter_rel_id, specification_id, specification_name,
               evaluation_type, min_value, max_value, acceptance_criteria, sequence,
               create_date, write_date, create_uid, write_uid)
            VALUES (%s, %s, %s, 'binary_selection', 0, 0, %s, %s, NOW(), NOW(), 1, 1)
        """, (rel04, spec_id, name, criteria, seq * 10))

env.cr.commit()
print("\nLISTO — SPHMC78 (HPV E7) y SPHMC79 (CARBA 5en1) configuradas con parámetros cualitativos.")
print("Verificar en staging: crear un análisis de QC para cada producto y validar el formulario.")
print("IMPORTANTE: revisar rangos MAVI-09 y criterios MAVI-07 contra los CERST de HPV E7 y CARBA 5en1.")
