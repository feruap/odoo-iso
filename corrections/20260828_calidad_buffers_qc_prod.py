"""
Corrección: sincronizar QC de buffers y reactivos de extracción con staging.

1. STBPR04 — agregar 5 especificaciones (tiene rels pero 0 specs) + crear punto de control
2. STBPR02 — agregar "Muestra positiva" MAVI-07 que faltaba
3. STBHE01 — agregar 3 parámetros QC (MAVI-07/09/13) + 5 specs + vincular al QP 304
4. STREX01/02 — agregar MAVI-13 "Partículas en solución" (rel y spec)

Referencia: STBPR03 (ya correcto en producción).
Confirmado por Diana Flores, 2026-08-28.
Idempotente — seguro de correr más de una vez.
"""

# ── 1. STBPR04 — specs a rels existentes (3278/3279/3280) ───────────────────────
env.cr.execute("""
    INSERT INTO amunet_quality_parameter_specification_config
      (product_parameter_rel_id, specification_id, specification_name, evaluation_type,
       acceptance_criteria, sequence, active, create_uid, write_uid, create_date, write_date)
    SELECT vals.rel_id, vals.spec_id, vals.spec_name, vals.eval_type, vals.criteria, vals.seq,
           true, 2, 2, NOW(), NOW()
    FROM (VALUES
      (3278, 629, 'Muestra positiva',        'mavi_07_ternary',  '#1-4 y/o #5 (patrón PRB-01)', 10),
      (3278, 628, 'Muestra negativa',        'mavi_07_ternary',  '#5 y/o #1-4 (patrón PRB-01)', 20),
      (3279, 146, 'Liberación de conjugado', 'numeric_range',    '1 a 30 segundos',              10),
      (3279, 126, 'Migración de conjugado',  'numeric_range',    '30 a 180 segundos',            20),
      (3280,  74, 'Partículas en solución',  'binary_selection', 'Sin partículas suspendidas',   10)
    ) AS vals(rel_id, spec_id, spec_name, eval_type, criteria, seq)
    WHERE NOT EXISTS (
      SELECT 1 FROM amunet_quality_parameter_specification_config sc2
      WHERE sc2.product_parameter_rel_id = vals.rel_id
        AND sc2.specification_id = vals.spec_id AND sc2.active = true
    )
""")
env.cr.execute("SELECT COUNT(*) FROM amunet_quality_parameter_specification_config WHERE product_parameter_rel_id IN (3278,3279,3280) AND active=true")
print(f"STBPR04 specs: {env.cr.fetchone()[0]} (esperado 5)")

# ── 2. STBPR04 — crear punto de control ─────────────────────────────────────────
env.cr.execute("SELECT id FROM amunet_quality_point WHERE name='Vial con solución de corrimiento para pruebas HV'")
row = env.cr.fetchone()
if not row:
    env.cr.execute("""
        INSERT INTO amunet_quality_point (name, company_id, active, create_uid, write_uid, create_date, write_date)
        VALUES ('Vial con solución de corrimiento para pruebas HV', 1, true, 2, 2, NOW(), NOW())
        RETURNING id
    """)
    qp_id = env.cr.fetchone()[0]
    env.cr.execute("""
        INSERT INTO amunet_quality_point_product_product_rel (amunet_quality_point_id, product_product_id)
        VALUES (%s, 1554)
    """, [qp_id])
    env.cr.execute("""
        INSERT INTO amunet_quality_point_stock_picking_type_rel (amunet_quality_point_id, stock_picking_type_id)
        VALUES (%s, 1)
    """, [qp_id])
    print(f"STBPR04 QP creado: id={qp_id}")
else:
    print(f"STBPR04 QP ya existe: id={row[0]}")

# ── 3. STBPR02 — agregar Muestra positiva MAVI-07 (rel_id=102) ──────────────────
env.cr.execute("""
    INSERT INTO amunet_quality_parameter_specification_config
      (product_parameter_rel_id, specification_id, specification_name, evaluation_type,
       acceptance_criteria, sequence, active, create_uid, write_uid, create_date, write_date)
    SELECT 102, 629, 'Muestra positiva', 'mavi_07_ternary', '#1-4 y/o #5 (patrón PRB-01)', 5, true, 2, 2, NOW(), NOW()
    WHERE NOT EXISTS (
      SELECT 1 FROM amunet_quality_parameter_specification_config sc2
      WHERE sc2.product_parameter_rel_id=102 AND sc2.specification_id=629 AND sc2.active=true
    )
""")
env.cr.execute("SELECT COUNT(*) FROM amunet_quality_parameter_specification_config WHERE product_parameter_rel_id=102 AND active=true")
print(f"STBPR02 MAVI-07 specs: {env.cr.fetchone()[0]} (esperado 2)")

# ── 4. STBHE01 — parámetros + specs ─────────────────────────────────────────────
# Crear rels si no existen
for param_id, param_code in [(65, 'MAVI-07'), (69, 'MAVI-09'), (71, 'MAVI-13')]:
    env.cr.execute("""
        INSERT INTO amunet_quality_parameter_product_rel
          (product_tmpl_id, parameter_id, parameter_code, create_uid, write_uid, create_date, write_date)
        SELECT 2321, %s, %s, 2, 2, NOW(), NOW()
        WHERE NOT EXISTS (
          SELECT 1 FROM amunet_quality_parameter_product_rel r2
          WHERE r2.product_tmpl_id=2321 AND r2.parameter_code=%s
        )
    """, [param_id, param_code, param_code])

# Agregar specs
env.cr.execute("""
    INSERT INTO amunet_quality_parameter_specification_config
      (product_parameter_rel_id, specification_id, specification_name, evaluation_type,
       acceptance_criteria, sequence, active, create_uid, write_uid, create_date, write_date)
    SELECT r.id, vals.spec_id, vals.spec_name, vals.eval_type, vals.criteria, vals.seq, true, 2, 2, NOW(), NOW()
    FROM amunet_quality_parameter_product_rel r
    JOIN (VALUES
      ('MAVI-07', 629, 'Muestra positiva',        'mavi_07_ternary',  '#1-4 y/o #5 (patrón PRB-01)', 10),
      ('MAVI-07', 628, 'Muestra negativa',         'mavi_07_ternary',  '#5 y/o #1-4 (patrón PRB-01)', 20),
      ('MAVI-09', 146, 'Liberación de conjugado', 'numeric_range',    '1 a 30 segundos',              10),
      ('MAVI-09', 126, 'Migración de conjugado',  'numeric_range',    '30 a 180 segundos',            20),
      ('MAVI-13',  74, 'Partículas en solución',  'binary_selection', 'Sin partículas suspendidas',   10)
    ) AS vals(pcode, spec_id, spec_name, eval_type, criteria, seq) ON r.parameter_code=vals.pcode
    WHERE r.product_tmpl_id=2321
      AND NOT EXISTS (
        SELECT 1 FROM amunet_quality_parameter_specification_config sc2
        WHERE sc2.product_parameter_rel_id=r.id AND sc2.specification_id=vals.spec_id AND sc2.active=true
      )
""")
env.cr.execute("""
    SELECT COUNT(*) FROM amunet_quality_parameter_specification_config sc
    JOIN amunet_quality_parameter_product_rel r ON sc.product_parameter_rel_id=r.id
    WHERE r.product_tmpl_id=2321 AND sc.active=true
""")
print(f"STBHE01 specs: {env.cr.fetchone()[0]} (esperado 5)")

# Vincular al QP 304
env.cr.execute("""
    INSERT INTO amunet_quality_point_product_product_rel (amunet_quality_point_id, product_product_id)
    SELECT 304, 2147
    WHERE NOT EXISTS (
      SELECT 1 FROM amunet_quality_point_product_product_rel r2
      WHERE r2.amunet_quality_point_id=304 AND r2.product_product_id=2147
    )
""")
print("STBHE01 vinculado a QP 304")

# ── 5. STREX01/02 — agregar MAVI-13 ─────────────────────────────────────────────
for pt_id, default_code in [(1007, 'STREX01'), (1008, 'STREX02')]:
    env.cr.execute("""
        INSERT INTO amunet_quality_parameter_product_rel
          (product_tmpl_id, parameter_id, parameter_code, create_uid, write_uid, create_date, write_date)
        SELECT %s, 71, 'MAVI-13', 2, 2, NOW(), NOW()
        WHERE NOT EXISTS (
          SELECT 1 FROM amunet_quality_parameter_product_rel r2
          WHERE r2.product_tmpl_id=%s AND r2.parameter_code='MAVI-13'
        )
    """, [pt_id, pt_id])
    env.cr.execute("""
        INSERT INTO amunet_quality_parameter_specification_config
          (product_parameter_rel_id, specification_id, specification_name, evaluation_type,
           acceptance_criteria, binary_option_pass, binary_option_fail, sequence, active,
           create_uid, write_uid, create_date, write_date)
        SELECT r.id, 74, 'Partículas en solución', 'binary_selection', 'Sin partículas suspendidas',
               'Sin Partículas En Solución', 'Con Partículas En Solución', 10, true, 2, 2, NOW(), NOW()
        FROM amunet_quality_parameter_product_rel r
        WHERE r.product_tmpl_id=%s AND r.parameter_code='MAVI-13'
          AND NOT EXISTS (
            SELECT 1 FROM amunet_quality_parameter_specification_config sc2
            WHERE sc2.product_parameter_rel_id=r.id AND sc2.specification_id=74 AND sc2.active=true
          )
    """, [pt_id])
    print(f"{default_code} MAVI-13 agregado")

print("\n✓ Script completado.")
