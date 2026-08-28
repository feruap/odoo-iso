"""
Corrección de análisis abiertos de cartuchos en PRODUCCIÓN.

1. Agregar spec "Letra adecuada" (specification_id=702) a todos los análisis
   abiertos de cartuchos (MPCAR*) que no la tienen en su línea MAVI-04.

2. Corregir texto de aceptación MPCAR79 ventana largo:
   "Máximo 18 mm" → "Máximo 21 mm" (el max_value ya estaba en 21, solo faltaba el texto).

Confirmado por Diana Flores, 2026-08-28.
Idempotente.
"""

# ── 1. Agregar "Letra adecuada" a análisis abiertos ─────────────────────────────
env.cr.execute("""
    INSERT INTO amunet_quality_test_line_detail
      (test_line_id, check_id, specification_id, specification_config_id,
       name, evaluation_type, acceptance_criteria,
       sequence, create_uid, write_uid, create_date, write_date)
    SELECT
      tl.id,
      qc.id,
      702,
      sc.id,
      'Letra adecuada',
      'binary_selection',
      'Información fácil de entender, letra con tono uniforme y definida.',
      (SELECT COALESCE(MAX(td2.sequence), 0) + 10
       FROM amunet_quality_test_line_detail td2 WHERE td2.test_line_id=tl.id),
      2, 2, NOW(), NOW()
    FROM amunet_quality_check qc
    JOIN product_product pp ON pp.id=qc.product_id
    JOIN product_template pt ON pt.id=pp.product_tmpl_id
    JOIN amunet_quality_test_line tl ON tl.check_id=qc.id
    JOIN amunet_quality_check_parameter p ON p.id=tl.parameter_id AND p.code='MAVI-04'
    JOIN amunet_quality_parameter_product_rel r ON r.product_tmpl_id=pt.id AND r.parameter_code='MAVI-04'
    JOIN amunet_quality_parameter_specification_config sc
      ON sc.product_parameter_rel_id=r.id AND sc.specification_id=702 AND sc.active=true
    WHERE pt.default_code LIKE 'MPCAR%%'
      AND qc.state NOT IN ('done','cancel')
      AND NOT EXISTS (
        SELECT 1 FROM amunet_quality_test_line_detail td2
        WHERE td2.test_line_id=tl.id AND td2.specification_id=702
      )
""")
env.cr.execute("""
    SELECT COUNT(*) FROM amunet_quality_check qc
    JOIN product_product pp ON pp.id=qc.product_id
    JOIN product_template pt ON pt.id=pp.product_tmpl_id
    JOIN amunet_quality_test_line tl ON tl.check_id=qc.id
    JOIN amunet_quality_check_parameter p ON p.id=tl.parameter_id AND p.code='MAVI-04'
    WHERE pt.default_code LIKE 'MPCAR%%' AND qc.state NOT IN ('done','cancel')
      AND NOT EXISTS (
        SELECT 1 FROM amunet_quality_test_line_detail td2
        WHERE td2.test_line_id=tl.id AND td2.specification_id=702
      )
""")
pendientes = env.cr.fetchone()[0]
print(f"Análisis sin Letra adecuada después: {pendientes} (esperado 0)")

# ── 2. Corregir texto ventana largo MPCAR79 ──────────────────────────────────────
env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config sc
    SET acceptance_criteria = 'Máximo 21 mm', write_date = NOW()
    FROM amunet_quality_parameter_product_rel r
    JOIN product_template pt ON r.product_tmpl_id=pt.id
    WHERE sc.product_parameter_rel_id=r.id
      AND pt.default_code='MPCAR79'
      AND sc.specification_name ILIKE '%%ventana%%largo%%'
      AND sc.acceptance_criteria ILIKE '%%18%%'
""")
print("MPCAR79 ventana largo: texto corregido a 'Máximo 21 mm'")

print("\n✓ Script completado.")
