"""
Configura los parámetros de QC de STBPR01-04 (soluciones de corrimiento PR):
  3 parámetros: MAVI-07 (visualización), MAVI-09 (tiempos), MAVI-13 (partículas).
  Tiempos estándar: Liberación 1–30 s / Migración 30–180 s.
  Confirmado por Diana Flores, 2026-08-04.

Para STBPR01-03: limpiar specs duplicadas, conservar las con FK refs.
Para STBPR04: crear los 3 rels y sus specs desde cero.

IDs de rels:
  STBPR01: MAVI-07=101, MAVI-09=98, MAVI-13=95
  STBPR02: MAVI-07=102, MAVI-09=99, MAVI-13=96
  STBPR03: MAVI-07=100, MAVI-09=97, MAVI-13=94
  STBPR04: sin rels → crear (tmpl_id=1726, param_ids: MAVI-07=65, MAVI-09=69, MAVI-13=71)

Canonical specs con TLD refs:
  STBPR01 MAVI-07: 78008(Neg,1), 78009(Pos,1), 78224(Interpretación,2→redir→78008)
  STBPR01 MAVI-09: 78222(Lib,2), 78223(Mig,2)  MAVI-13: 78221(2)
  STBPR02 MAVI-07: 78214(Interpretación,1→convertir→Neg)
  STBPR02 MAVI-09: 78212(Lib,1), 78213(Mig,1)  MAVI-13: 78211(1)
  STBPR03 MAVI-07: 78003(Neg,3), 78004(Pos,3), 78219(Interpretación,4→redir→78003)
  STBPR03 MAVI-09: 78217(Lib,4), 78218(Mig,4)  MAVI-13: 78216(4)

Idempotente — seguro de correr más de una vez.
Correr UNA VEZ después del deploy a producción.
"""

Param    = env['amunet.quality.check.parameter']
ParamRel = env['amunet.quality.parameter.product.rel']

# ═══════════════════════════════════════════════════════════════════════════════
# STBPR01-03
# ═══════════════════════════════════════════════════════════════════════════════

PRODUCTOS = {
    'STBPR01': {
        # MAVI-07: 78008=Neg(keep), 78009=Pos(keep), 78224=Interpretación(redir→78008, delete)
        'mavi07_neg': 78008, 'mavi07_pos': 78009,
        'mavi07_redir_ids': [78224],   # TLDs de estos → 78008 (Neg), luego delete
        'rel07': 101,
        'del_mavi07': [74826,75419,75420,75539,75540,75737,75738,75953,75954,
                       76238,76239,76308,76309,76525,76526,76741,76742,76957,76958,
                       77173,77174,77792,77793],
        'canon_lib': 78222, 'canon_mig': 78223, 'canon_par': 78221,
        'del_mavi09': [155,156,75735,75736,75951,75952,76236,76237,76306,76307,
                       76523,76524,76739,76740,76955,76956,77171,77172,77790,77791,78006,78007],
        'del_mavi13': [151,75734,75950,76166,76522,76738,76954,77170,77789,78005],
    },
    'STBPR02': {
        # MAVI-07: 78214=Interpretación(1 ref → convertir en Neg), crear Pos nuevo
        'mavi07_neg': 78214, 'mavi07_pos': None,  # pos se crea nuevo
        'mavi07_redir_ids': [],
        'rel07': 102,
        'del_mavi07': [74827,75415,75416,75535,75536,75727,75728,75943,75944,
                       76230,76231,76300,76301,76515,76516,76731,76732,76947,76948,
                       77163,77164,77782,77783,77998,77999],
        'canon_lib': 78212, 'canon_mig': 78213, 'canon_par': 78211,
        'del_mavi09': [157,158,75725,75726,75941,75942,76228,76229,76298,76299,
                       76513,76514,76729,76730,76945,76946,77161,77162,77780,77781,77996,77997],
        'del_mavi13': [152,75724,75940,76156,76512,76728,76944,77160,77779,77995],
    },
    'STBPR03': {
        # MAVI-07: 78003=Neg(keep), 78004=Pos(keep), 78219=Interpretación(redir→78003, delete)
        'mavi07_neg': 78003, 'mavi07_pos': 78004,
        'mavi07_redir_ids': [78219],
        'rel07': 100,
        'del_mavi07': [74825,75417,75418,75537,75538,75732,75733,75948,75949,
                       76234,76235,76304,76305,76520,76521,76736,76737,76952,76953,
                       77168,77169,77787,77788],
        'canon_lib': 78217, 'canon_mig': 78218, 'canon_par': 78216,
        'del_mavi09': [153,154,75730,75731,75946,75947,76232,76233,76302,76303,
                       76518,76519,76734,76735,76950,76951,77166,77167,77785,77786,78001,78002],
        'del_mavi13': [150,75729,75945,76161,76517,76733,76949,77165,77784,78000],
    },
}

for code, cfg in PRODUCTOS.items():
    print(f"\n── {code} ──────────────────────────────")

    # ── MAVI-07 ──────────────────────────────────────────────────────────────
    # a) Redirigir TLDs de specs "Interpretación" → spec canónica Neg
    if cfg['mavi07_redir_ids']:
        env.cr.execute(
            "UPDATE amunet_quality_test_line_detail "
            "SET specification_config_id = %s "
            "WHERE specification_config_id = ANY(%s)",
            (cfg['mavi07_neg'], cfg['mavi07_redir_ids'])
        )
        print(f"  MAVI-07 TLDs redirigidas: {env.cr.rowcount} → id={cfg['mavi07_neg']}")

    # b) Actualizar spec Muestra negativa
    env.cr.execute("""
        UPDATE amunet_quality_parameter_specification_config
        SET specification_id = 628, specification_name = 'Muestra negativa',
            evaluation_type = 'mavi_07_ternary', min_value = 0, max_value = 0,
            acceptance_criteria = '#5 y/o #1-4 (patrón PRB-01)', sequence = 20,
            write_date = NOW()
        WHERE id = %s
    """, (cfg['mavi07_neg'],))
    print(f"  MAVI-07 Muestra negativa (id={cfg['mavi07_neg']}): actualizada")

    # c) Actualizar spec Muestra positiva si ya existe, o crear nueva
    if cfg['mavi07_pos']:
        env.cr.execute("""
            UPDATE amunet_quality_parameter_specification_config
            SET specification_id = 629, specification_name = 'Muestra positiva',
                evaluation_type = 'mavi_07_ternary', min_value = 0, max_value = 0,
                acceptance_criteria = '#1-4 y/o #5 (patrón PRB-01)', sequence = 10,
                write_date = NOW()
            WHERE id = %s
        """, (cfg['mavi07_pos'],))
        print(f"  MAVI-07 Muestra positiva (id={cfg['mavi07_pos']}): actualizada")
    else:
        env.cr.execute("""
            INSERT INTO amunet_quality_parameter_specification_config
              (product_parameter_rel_id, specification_id, specification_name,
               evaluation_type, min_value, max_value, acceptance_criteria, sequence,
               create_date, write_date, create_uid, write_uid)
            VALUES (%s, 629, 'Muestra positiva', 'mavi_07_ternary', 0, 0,
                    '#1-4 y/o #5 (patrón PRB-01)', 10, NOW(), NOW(), 1, 1)
            ON CONFLICT DO NOTHING
        """, (cfg['rel07'],))
        print(f"  MAVI-07 Muestra positiva: insertada (rel_id={cfg['rel07']})")

    # d) Borrar specs "Interpretación" y todos los demás duplicados de MAVI-07
    all_del07 = cfg['del_mavi07'] + cfg['mavi07_redir_ids']
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config WHERE id = ANY(%s)",
        (all_del07,)
    )
    print(f"  MAVI-07 duplicados eliminados: {env.cr.rowcount}")

    # ── MAVI-09 ──────────────────────────────────────────────────────────────
    env.cr.execute("""
        UPDATE amunet_quality_parameter_specification_config
        SET specification_id = 146, specification_name = 'Liberación de conjugado',
            evaluation_type = 'numeric_range', min_value = 1, max_value = 30,
            acceptance_criteria = '1 a 30 segundos', sequence = 10, write_date = NOW()
        WHERE id = %s
    """, (cfg['canon_lib'],))
    print(f"  MAVI-09 Lib (id={cfg['canon_lib']}): → 1–30 s")

    env.cr.execute("""
        UPDATE amunet_quality_parameter_specification_config
        SET specification_id = 126, specification_name = 'Migración de conjugado',
            evaluation_type = 'numeric_range', min_value = 30, max_value = 180,
            acceptance_criteria = '30 a 180 segundos', sequence = 20, write_date = NOW()
        WHERE id = %s
    """, (cfg['canon_mig'],))
    print(f"  MAVI-09 Mig (id={cfg['canon_mig']}): → 30–180 s")

    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config WHERE id = ANY(%s)",
        (cfg['del_mavi09'],)
    )
    print(f"  MAVI-09 duplicados eliminados: {env.cr.rowcount}")

    # ── MAVI-13 ──────────────────────────────────────────────────────────────
    env.cr.execute("""
        UPDATE amunet_quality_parameter_specification_config
        SET specification_id = 74, specification_name = 'Partículas en solución',
            evaluation_type = 'binary_selection', min_value = 0, max_value = 0,
            acceptance_criteria = 'Sin partículas suspendidas', sequence = 10, write_date = NOW()
        WHERE id = %s
    """, (cfg['canon_par'],))
    print(f"  MAVI-13 (id={cfg['canon_par']}): → Sin partículas suspendidas")

    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config WHERE id = ANY(%s)",
        (cfg['del_mavi13'],)
    )
    print(f"  MAVI-13 duplicados eliminados: {env.cr.rowcount}")

# ═══════════════════════════════════════════════════════════════════════════════
# STBPR04: crear rels y specs desde cero
# ═══════════════════════════════════════════════════════════════════════════════

print("\n── STBPR04 (crear parámetros desde cero) ────────")

tmpl_id_pr04 = 1726
params_pr04 = [
    (65, 'MAVI-07', 'Visualización de líneas "resultado base"'),
    (69, 'MAVI-09', 'Desempeño del tiempo de flujo capilar'),
    (71, 'MAVI-13', 'Bloqueo de la luz por partículas'),
]

for param_id, code, name in params_pr04:
    existing = ParamRel.search([
        ('product_tmpl_id', '=', tmpl_id_pr04),
        ('parameter_id', '=', param_id),
    ], limit=1)
    if not existing:
        rel = ParamRel.create({
            'product_tmpl_id': tmpl_id_pr04,
            'parameter_id':    param_id,
            'parameter_code':  code,
            'parameter_name':  name,
        })
        print(f"  {code} rel creada (id={rel.id})")
    else:
        print(f"  {code} rel ya existe (id={existing.id}), OK")

env.flush_all()

env.cr.execute("""
    SELECT rel.id, rel.parameter_code
    FROM amunet_quality_parameter_product_rel rel
    WHERE rel.product_tmpl_id = %s AND rel.parameter_id IN (65, 69, 71)
""", (tmpl_id_pr04,))
pr04_rels = {row[1]: row[0] for row in env.cr.fetchall()}
print(f"  STBPR04 rels: {pr04_rels}")

rel07 = pr04_rels.get('MAVI-07')
rel09 = pr04_rels.get('MAVI-09')
rel13 = pr04_rels.get('MAVI-13')

if rel07:
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config WHERE product_parameter_rel_id = %s",
        (rel07,)
    )
    env.cr.execute("""
        INSERT INTO amunet_quality_parameter_specification_config
          (product_parameter_rel_id, specification_id, specification_name,
           evaluation_type, min_value, max_value, acceptance_criteria, sequence,
           create_date, write_date, create_uid, write_uid)
        VALUES
          (%s, 629, 'Muestra positiva', 'mavi_07_ternary', 0, 0,
           '#1-4 y/o #5 (patrón PRB-01)', 10, NOW(), NOW(), 1, 1),
          (%s, 628, 'Muestra negativa', 'mavi_07_ternary', 0, 0,
           '#5 y/o #1-4 (patrón PRB-01)', 20, NOW(), NOW(), 1, 1)
    """, (rel07, rel07))
    print(f"  STBPR04 MAVI-07: 2 specs creadas")

if rel09:
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config WHERE product_parameter_rel_id = %s",
        (rel09,)
    )
    env.cr.execute("""
        INSERT INTO amunet_quality_parameter_specification_config
          (product_parameter_rel_id, specification_id, specification_name,
           evaluation_type, min_value, max_value, acceptance_criteria, sequence,
           create_date, write_date, create_uid, write_uid)
        VALUES
          (%s, 146, 'Liberación de conjugado', 'numeric_range', 1, 30,
           '1 a 30 segundos', 10, NOW(), NOW(), 1, 1),
          (%s, 126, 'Migración de conjugado', 'numeric_range', 30, 180,
           '30 a 180 segundos', 20, NOW(), NOW(), 1, 1)
    """, (rel09, rel09))
    print(f"  STBPR04 MAVI-09: 2 specs creadas (lib 1-30s, mig 30-180s)")

if rel13:
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config WHERE product_parameter_rel_id = %s",
        (rel13,)
    )
    env.cr.execute("""
        INSERT INTO amunet_quality_parameter_specification_config
          (product_parameter_rel_id, specification_id, specification_name,
           evaluation_type, min_value, max_value, acceptance_criteria, sequence,
           create_date, write_date, create_uid, write_uid)
        VALUES (%s, 74, 'Partículas en solución', 'binary_selection', 0, 0,
                'Sin partículas suspendidas', 10, NOW(), NOW(), 1, 1)
    """, (rel13,))
    print(f"  STBPR04 MAVI-13: 1 spec creada")

env.cr.commit()
print("\nLISTO — STBPR01-04: MAVI-07 + MAVI-09 (1-30/30-180s) + MAVI-13 configurados.")
print("Verificar: https://stagingfc.amunet.com.mx/odoo/quality-checks")
