"""
Corrección URGENTE: longitudes MAVI-11 de STHIS01-06 en producción.

Cambio: tolerancia ±2 mm → ±5 mm en todas las especificaciones de longitud
de los hisopos STHIS01 al STHIS06.

Aplica a:
  1. Especificaciones config activas (master) de los 6 hisopos
  2. Detalles (snapshot) de los análisis actualmente abiertos (in_progress/ready)

Fórmula: nominal = (max_value + min_value) / 2
         new_max = nominal + 5
         new_min = nominal - 5
Texto: "± 2 mm" → "± 5 mm" (regexp para capturar variantes de espacio)

Confirmado por Diana Flores, 2026-08-28.
Idempotente — sólo toca filas donde max-min = 4 (es decir, ±2 mm actuales).
"""

# ── 1. Especificaciones config activas → ±5 mm ──────────────────────────────────
env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config sc
    SET max_value = ROUND(((sc.max_value + sc.min_value) / 2) + 5, 2),
        min_value = ROUND(((sc.max_value + sc.min_value) / 2) - 5, 2),
        acceptance_criteria = regexp_replace(sc.acceptance_criteria, '[±] 2 mm', '± 5 mm'),
        write_date = NOW()
    FROM amunet_quality_parameter_product_rel r
    JOIN product_template pt ON r.product_tmpl_id = pt.id
    WHERE sc.product_parameter_rel_id = r.id
      AND r.parameter_code = 'MAVI-11'
      AND pt.default_code LIKE 'STHIS%'
      AND sc.active = true
      AND (sc.max_value - sc.min_value) = 4
""")
print(f"Spec configs MAVI-11 actualizadas (±5 mm): {env.cr.rowcount}")

# ── 2. Detalles en análisis abiertos → ±5 mm ───────────────────────────────────
env.cr.execute("""
    UPDATE amunet_quality_test_line_detail td
    SET max_value = ROUND(((td.max_value + td.min_value) / 2) + 5, 2),
        min_value = ROUND(((td.max_value + td.min_value) / 2) - 5, 2),
        acceptance_criteria = regexp_replace(td.acceptance_criteria, '[±] 2 mm', '± 5 mm'),
        write_date = NOW()
    FROM amunet_quality_test_line tl
    JOIN amunet_quality_check qc ON qc.id = tl.check_id
    JOIN amunet_quality_check_parameter p ON p.id = tl.parameter_id AND p.code = 'MAVI-11'
    JOIN product_product pp ON pp.id = qc.product_id
    JOIN product_template pt ON pt.id = pp.product_tmpl_id
    WHERE td.test_line_id = tl.id
      AND pt.default_code LIKE 'STHIS%'
      AND qc.state NOT IN ('done', 'cancel')
      AND (td.max_value - td.min_value) = 4
""")
print(f"Detalles en análisis abiertos actualizados (±5 mm): {env.cr.rowcount}")

# ── Verificación ────────────────────────────────────────────────────────────────
env.cr.execute("""
    SELECT qc.id, pt.default_code, td.name, td.acceptance_criteria, td.max_value, td.min_value
    FROM amunet_quality_test_line_detail td
    JOIN amunet_quality_test_line tl ON tl.id = td.test_line_id
    JOIN amunet_quality_check qc ON qc.id = tl.check_id
    JOIN amunet_quality_check_parameter p ON p.id = tl.parameter_id AND p.code = 'MAVI-11'
    JOIN product_product pp ON pp.id = qc.product_id
    JOIN product_template pt ON pt.id = pp.product_tmpl_id
    WHERE pt.default_code LIKE 'STHIS%'
      AND qc.state NOT IN ('done', 'cancel')
    ORDER BY qc.id, td.name
""")
rows = env.cr.fetchall()
errores = 0
for r in rows:
    rango = r[4] - r[5]
    ok = "✓" if rango == 10 else "✗"
    if rango != 10:
        errores += 1
    print(f"  {ok} análisis {r[0]} {r[1]} | {r[2]}: {r[3]} | max={r[4]} min={r[5]}")

if errores == 0:
    print(f"\n✓ Script completado: {len(rows)} detalles, todos ±5 mm.")
else:
    print(f"\n✗ {errores} fila(s) con rango distinto de 10 — revisar.")
