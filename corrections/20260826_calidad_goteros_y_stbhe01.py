"""
Correcciones de QC para goteros, MPCAR79 y STBHE01.
Confirmado por Diana Flores, 2026-08-26.

1. STGOT02 MAVI-17 — Conteo de gotas: 5–10 µL ± 2µL  (antes: 4–11 sin nominal)
2. STGOT02 MAVI-11 — Punta del gotero:  nominal 21 mm ± 5 mm (16–26)
3. STGOT02 MAVI-11 — Largo del gotero:  nominal 78 mm ± 5 mm (73–83)
4. STGOT03 MAVI-11 — Punta del gotero:  nominal 22 mm ± 5 mm (17–27)
5. STGOT03 MAVI-11 — Largo del gotero:  nominal 99 mm ± 5 mm (94–104)
6. STBHE01 — report_document_code = RAST-014, descripción y referencias ESPST-014
7. MPCAR79 MAVI-11 — Interna (Ventana) Largo: máximo 21 mm (antes 18 mm)
   Nota: cambio exclusivo para MPCAR79; los demás cartuchos impares no se tocan.

Idempotente — seguro de correr más de una vez.
Correr UNA VEZ después del deploy a producción.
"""

# ── 1. STGOT02 MAVI-17 — Conteo de gotas: 5–10 µL ±2 ──────────────────────────
env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config sc
    SET min_value     = 5,
        max_value     = 10,
        nominal_value = 7.5,
        tolerance     = 2,
        write_date    = NOW()
    FROM amunet_quality_parameter_product_rel r
    JOIN product_template pt ON r.product_tmpl_id = pt.id
    WHERE sc.product_parameter_rel_id = r.id
      AND pt.default_code = 'STGOT02'
      AND r.parameter_code = 'MAVI-17'
      AND sc.specification_name ILIKE '%gota%'
""")
print("STGOT02 MAVI-17 Conteo de gotas: → 5–10 µL ±2")

# ── 2-3. STGOT02 MAVI-11 — Punta (21±5) y Largo (78±5) ────────────────────────
env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config sc
    SET nominal_value = 21,
        tolerance     = 5,
        min_value     = 16,
        max_value     = 26,
        write_date    = NOW()
    FROM amunet_quality_parameter_product_rel r
    JOIN product_template pt ON r.product_tmpl_id = pt.id
    WHERE sc.product_parameter_rel_id = r.id
      AND pt.default_code = 'STGOT02'
      AND r.parameter_code = 'MAVI-11'
      AND sc.specification_name ILIKE '%punta%'
""")
print("STGOT02 MAVI-11 Punta: → 21 ±5 mm")

env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config sc
    SET nominal_value = 78,
        tolerance     = 5,
        min_value     = 73,
        max_value     = 83,
        write_date    = NOW()
    FROM amunet_quality_parameter_product_rel r
    JOIN product_template pt ON r.product_tmpl_id = pt.id
    WHERE sc.product_parameter_rel_id = r.id
      AND pt.default_code = 'STGOT02'
      AND r.parameter_code = 'MAVI-11'
      AND sc.specification_name ILIKE '%largo%'
""")
print("STGOT02 MAVI-11 Largo: → 78 ±5 mm")

# ── 4-5. STGOT03 MAVI-11 — Punta (22±5) y Largo (99±5) ────────────────────────
env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config sc
    SET nominal_value = 22,
        tolerance     = 5,
        min_value     = 17,
        max_value     = 27,
        write_date    = NOW()
    FROM amunet_quality_parameter_product_rel r
    JOIN product_template pt ON r.product_tmpl_id = pt.id
    WHERE sc.product_parameter_rel_id = r.id
      AND pt.default_code = 'STGOT03'
      AND r.parameter_code = 'MAVI-11'
      AND sc.specification_name ILIKE '%punta%'
""")
print("STGOT03 MAVI-11 Punta: → 22 ±5 mm")

env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config sc
    SET nominal_value = 99,
        tolerance     = 5,
        min_value     = 94,
        max_value     = 104,
        write_date    = NOW()
    FROM amunet_quality_parameter_product_rel r
    JOIN product_template pt ON r.product_tmpl_id = pt.id
    WHERE sc.product_parameter_rel_id = r.id
      AND pt.default_code = 'STGOT03'
      AND r.parameter_code = 'MAVI-11'
      AND sc.specification_name ILIKE '%largo%'
""")
print("STGOT03 MAVI-11 Largo: → 99 ±5 mm")

# ── 6. STBHE01 — product_template ──────────────────────────────────────────────
env.cr.execute("""
    UPDATE product_template
    SET report_document_code = 'RAST-014',
        description = jsonb_build_object('es_MX', 'Solución de corrimiento para muestras de heces'),
        report_references = '- Especificaciones ESPST-014
- Técnica de análisis TAST-014
- Inspección de Insumos PNOCC-002
- Método de muestreo de acuerdo a la norma ANSI / ASQ Z1.4 PNOCC-005',
        write_date = NOW()
    WHERE default_code = 'STBHE01'
""")
print("STBHE01: report_document_code=RAST-014, descripción y referencias actualizadas")

# ── 7. MPCAR79 MAVI-11 — Interna (Ventana) Largo: máx 18 → 21 mm ──────────────
env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config sc
    SET max_value     = 21,
        nominal_value = 10.5,
        tolerance     = 10.5,
        write_date    = NOW()
    FROM amunet_quality_parameter_product_rel r
    JOIN product_template pt ON r.product_tmpl_id = pt.id
    WHERE sc.product_parameter_rel_id = r.id
      AND pt.default_code = 'MPCAR79'
      AND r.parameter_code = 'MAVI-11'
      AND sc.specification_name ILIKE '%ventana%largo%'
""")
print("MPCAR79 MAVI-11 Interna (Ventana) Largo: → máx 21 mm")

print("\\n✓ Script completado.")
