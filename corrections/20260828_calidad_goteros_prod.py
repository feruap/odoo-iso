"""
Corrección de goteros en PRODUCCIÓN — análisis abiertos.

1. Agregar MAVI-17 (volumen/tamaño de gota) a los 8 análisis abiertos de goteros
   que todavía tienen VAMA-038 como snapshot y no tienen línea MAVI-17.
   Criterios por gotero:
     STGOT01: 10 µl ±5 µl  (5–15)
     STGOT02: 5 a 10 µl ±2 µl  (5–10, según Diana/PM)
     STGOT03: 20 µl ±5 µl  (15–25)
     STGOT04: 25 µl ±5 µl  (20–30)
     STGOT05: 40 µl ±5 µl  (35–45)
     STGOT06: 40 µl ±5 µl  (35–45)
     STGOT07: 20 µl ±5 µl  (15–25)
2. Corregir STGOT02/03 MAVI-11 en los análisis: valores ±1 mm → ±5 mm.
3. Corregir texto vacío de STGOT02 MAVI-17 en spec config.

NOTA: Letra adecuada NO aplica a goteros — no se agrega.

Confirmado por Diana Flores, 2026-08-28. Idempotente.
"""

CHECK_IDS = [373, 374, 375, 376, 377, 378, 379, 753]

# ── 1. Agregar test_line MAVI-17 a análisis que no la tienen ────────────────────
env.cr.execute("""
    INSERT INTO amunet_quality_test_line
      (check_id, parameter_id, parameter_rel_id, create_uid, write_uid, create_date, write_date)
    SELECT qc.id, r.parameter_id, r.id, 2, 2, NOW(), NOW()
    FROM amunet_quality_check qc
    JOIN product_product pp ON pp.id=qc.product_id
    JOIN product_template pt ON pt.id=pp.product_tmpl_id
    JOIN amunet_quality_parameter_product_rel r ON r.product_tmpl_id=pt.id AND r.parameter_code='MAVI-17'
    WHERE qc.id = ANY(%s)
      AND NOT EXISTS (
        SELECT 1 FROM amunet_quality_test_line tl2
        JOIN amunet_quality_check_parameter p2 ON p2.id=tl2.parameter_id
        WHERE tl2.check_id=qc.id AND p2.code='MAVI-17'
      )
""", [CHECK_IDS])

# ── 2. Agregar detalle MAVI-17 con criterio correcto por gotero ─────────────────
env.cr.execute("""
    INSERT INTO amunet_quality_test_line_detail
      (test_line_id, check_id, specification_id, specification_config_id,
       name, evaluation_type, acceptance_criteria, max_value, min_value,
       sequence, create_uid, write_uid, create_date, write_date)
    SELECT tl.id, qc.id, sc.specification_id, sc.id,
           sc.specification_name, sc.evaluation_type,
           CASE pt.default_code
             WHEN 'STGOT01' THEN '10 µl ±5 µl'
             WHEN 'STGOT02' THEN '5 a 10 µl ±2 µl'
             WHEN 'STGOT03' THEN '20 µl ±5 µl'
             WHEN 'STGOT04' THEN '25 µl ±5 µl'
             WHEN 'STGOT05' THEN '40 µl ±5 µl'
             WHEN 'STGOT06' THEN '40 µl ±5 µl'
             WHEN 'STGOT07' THEN '20 µl ±5 µl'
             ELSE sc.acceptance_criteria
           END,
           sc.max_value, sc.min_value,
           10, 2, 2, NOW(), NOW()
    FROM amunet_quality_check qc
    JOIN product_product pp ON pp.id=qc.product_id
    JOIN product_template pt ON pt.id=pp.product_tmpl_id
    JOIN amunet_quality_test_line tl ON tl.check_id=qc.id
    JOIN amunet_quality_check_parameter p ON p.id=tl.parameter_id AND p.code='MAVI-17'
    JOIN amunet_quality_parameter_product_rel r ON r.id=tl.parameter_rel_id
    JOIN amunet_quality_parameter_specification_config sc
      ON sc.product_parameter_rel_id=r.id AND sc.active=true
    WHERE qc.id = ANY(%s)
      AND NOT EXISTS (
        SELECT 1 FROM amunet_quality_test_line_detail td2
        WHERE td2.test_line_id=tl.id AND td2.specification_id=sc.specification_id
      )
""", [CHECK_IDS])
print("MAVI-17 detalles con criterio por gotero: agregados")

# ── 3. Corregir STGOT02/03 MAVI-11 en análisis (±1 → ±5) ──────────────────────
env.cr.execute("""
    UPDATE amunet_quality_test_line_detail td
    SET max_value = sc.max_value,
        min_value = sc.min_value,
        acceptance_criteria = sc.acceptance_criteria,
        write_date = NOW()
    FROM amunet_quality_test_line tl
    JOIN amunet_quality_check qc ON qc.id=tl.check_id
    JOIN amunet_quality_check_parameter p ON p.id=tl.parameter_id AND p.code='MAVI-11'
    JOIN amunet_quality_parameter_product_rel r ON r.id=tl.parameter_rel_id
    JOIN amunet_quality_parameter_specification_config sc
      ON sc.product_parameter_rel_id=r.id AND sc.specification_id=td.specification_id AND sc.active=true
    WHERE td.test_line_id=tl.id AND qc.id = ANY(%s)
""", [CHECK_IDS])
print("MAVI-11 corregido (±5) en análisis STGOT02/03")

# ── 4. Corregir texto STGOT02 MAVI-17 en spec config ───────────────────────────
env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config sc
    SET acceptance_criteria = '5 a 10 µl ±2 µl', write_date = NOW()
    FROM amunet_quality_parameter_product_rel r
    JOIN product_template pt ON r.product_tmpl_id=pt.id
    WHERE sc.product_parameter_rel_id=r.id
      AND pt.default_code='STGOT02' AND r.parameter_code='MAVI-17'
      AND (sc.acceptance_criteria IS NULL OR sc.acceptance_criteria='')
""")
print("STGOT02 MAVI-17 spec config: texto corregido")

print("\n✓ Script completado.")
