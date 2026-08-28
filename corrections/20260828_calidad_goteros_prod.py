"""
Corrección de goteros en PRODUCCIÓN — análisis abiertos y spec configs.

1. Agregar MAVI-17 (Conteo de gotas) a los 8 análisis abiertos de goteros
   que todavía muestran VAMA-038 como snapshot y no tienen línea MAVI-17.
2. Agregar "Letra adecuada" (spec 702) a MAVI-04 en esos mismos análisis.
3. Corregir STGOT02/03 MAVI-11: los análisis tienen valores ±1 (viejos);
   actualizarlos con los valores ±5 del spec config actual.
4. Corregir texto de STGOT02 MAVI-17 acceptance_criteria (estaba vacío).

Confirmado por Diana Flores, 2026-08-28. Idempotente.
"""

import json

# IDs de los 8 análisis abiertos de goteros en producción
CHECK_IDS = [373, 374, 375, 376, 377, 378, 379, 753]

# ── 1. Agregar MAVI-17 a los análisis que no lo tienen ──────────────────────────
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
print("MAVI-17 test_lines agregadas")

# Agregar detalles MAVI-17 a las nuevas líneas
env.cr.execute("""
    INSERT INTO amunet_quality_test_line_detail
      (test_line_id, check_id, specification_id, specification_config_id,
       name, evaluation_type, acceptance_criteria, max_value, min_value,
       sequence, create_uid, write_uid, create_date, write_date)
    SELECT tl.id, qc.id, sc.specification_id, sc.id,
           sc.specification_name, sc.evaluation_type,
           COALESCE(NULLIF(sc.acceptance_criteria,''), sc.specification_name),
           sc.max_value, sc.min_value,
           10, 2, 2, NOW(), NOW()
    FROM amunet_quality_check qc
    JOIN product_product pp ON pp.id=qc.product_id
    JOIN product_template pt ON pt.id=pp.product_tmpl_id
    JOIN amunet_quality_test_line tl ON tl.check_id=qc.id
    JOIN amunet_quality_check_parameter p ON p.id=tl.parameter_id AND p.code='MAVI-17'
    JOIN amunet_quality_parameter_product_rel r ON r.product_tmpl_id=pt.id AND r.parameter_code='MAVI-17'
    JOIN amunet_quality_parameter_specification_config sc
      ON sc.product_parameter_rel_id=r.id AND sc.active=true
    WHERE qc.id = ANY(%s)
      AND NOT EXISTS (
        SELECT 1 FROM amunet_quality_test_line_detail td2
        WHERE td2.test_line_id=tl.id AND td2.specification_id=sc.specification_id
      )
""", [CHECK_IDS])
print("MAVI-17 detalles agregados")

# ── 2. Agregar "Letra adecuada" a MAVI-04 en los análisis de goteros ────────────
env.cr.execute("""
    INSERT INTO amunet_quality_test_line_detail
      (test_line_id, check_id, specification_id, specification_config_id,
       name, evaluation_type, acceptance_criteria,
       sequence, create_uid, write_uid, create_date, write_date)
    SELECT tl.id, qc.id, 702, sc.id,
           'Letra adecuada', 'binary_selection',
           'Información fácil de entender, letra con tono uniforme y definida.',
           (SELECT COALESCE(MAX(td2.sequence),0)+10 FROM amunet_quality_test_line_detail td2 WHERE td2.test_line_id=tl.id),
           2, 2, NOW(), NOW()
    FROM amunet_quality_check qc
    JOIN product_product pp ON pp.id=qc.product_id
    JOIN product_template pt ON pt.id=pp.product_tmpl_id
    JOIN amunet_quality_test_line tl ON tl.check_id=qc.id
    JOIN amunet_quality_check_parameter p ON p.id=tl.parameter_id AND p.code='MAVI-04'
    JOIN amunet_quality_parameter_product_rel r ON r.product_tmpl_id=pt.id AND r.parameter_code='MAVI-04'
    JOIN amunet_quality_parameter_specification_config sc
      ON sc.product_parameter_rel_id=r.id AND sc.specification_id=702 AND sc.active=true
    WHERE qc.id = ANY(%s)
      AND NOT EXISTS (
        SELECT 1 FROM amunet_quality_test_line_detail td2
        WHERE td2.test_line_id=tl.id AND td2.specification_id=702
      )
""", [CHECK_IDS])
print("Letra adecuada en goteros: agregada")

# ── 3. Corregir MAVI-11 en análisis de STGOT02/03 (valores ±1 → ±5) ────────────
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
print("MAVI-11 detalles corregidos con valores actuales del spec config")

# ── 4. Corregir spec config STGOT02 MAVI-17 acceptance_criteria vacío ───────────
env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config sc
    SET acceptance_criteria = '5 a 10 µl ±2 µl', write_date = NOW()
    FROM amunet_quality_parameter_product_rel r
    JOIN product_template pt ON r.product_tmpl_id=pt.id
    WHERE sc.product_parameter_rel_id=r.id
      AND pt.default_code='STGOT02'
      AND r.parameter_code='MAVI-17'
      AND (sc.acceptance_criteria IS NULL OR sc.acceptance_criteria='')
""")
print("STGOT02 MAVI-17 acceptance_criteria corregido")

# Resumen
for check_id in CHECK_IDS:
    env.cr.execute("""
        SELECT p.code, COUNT(td.id) AS detalles
        FROM amunet_quality_test_line tl
        JOIN amunet_quality_check_parameter p ON p.id=tl.parameter_id
        LEFT JOIN amunet_quality_test_line_detail td ON td.test_line_id=tl.id
        WHERE tl.check_id=%s GROUP BY p.code ORDER BY p.code
    """, [check_id])
    rows = env.cr.fetchall()
    summary = ', '.join(f"{r[0]}:{r[1]}" for r in rows)
    print(f"  Análisis {check_id}: {summary}")

print("\n✓ Script completado.")
