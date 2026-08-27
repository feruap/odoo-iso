"""
Corrección MAVI-04 en todos los cartuchos (MPCAR/MPCAC):
1. Agrega spec 'Letra adecuada' a los cartuchos que no la tienen.
2. Elimina el duplicado 'rasgaduras' (minúscula) que existía en algunos.
Confirmado por Diana Flores, 2026-08-27.

Idempotente — seguro de correr más de una vez.
Correr UNA VEZ después del deploy a producción.
Nota: no toca MPCAR26/36/77/78/79 ni MPCAC11 (tienen estructura diferente).
"""

# ── 1. Agregar 'Letra adecuada' a cartuchos que no la tienen ────────────────
env.cr.execute("""
    INSERT INTO amunet_quality_parameter_specification_config
      (product_parameter_rel_id, specification_id, specification_name,
       evaluation_type, acceptance_criteria,
       binary_option_pass, binary_option_fail,
       sequence, active, create_uid, write_uid, create_date, write_date)
    SELECT
      r.id,
      702,
      'Letra adecuada',
      'binary_selection',
      'Información fácil de entender, letra con tono uniforme y definida.',
      'Letra Adecuada',
      'Letra No Adecuada',
      10,
      true,
      2, 2, NOW(), NOW()
    FROM amunet_quality_parameter_product_rel r
    JOIN product_template pt ON r.product_tmpl_id = pt.id
    WHERE (pt.default_code LIKE 'MPCAR%%' OR pt.default_code LIKE 'MPCAC%%')
      AND pt.active = true
      AND r.parameter_code = 'MAVI-04'
      AND pt.default_code NOT IN ('MPCAR26','MPCAR36','MPCAR77','MPCAR78','MPCAR79','MPCAC11')
      AND NOT EXISTS (
        SELECT 1 FROM amunet_quality_parameter_specification_config sc2
        WHERE sc2.product_parameter_rel_id = r.id
          AND sc2.specification_name ILIKE '%%letra%%'
      )
""")
env.cr.execute("SELECT COUNT(*) FROM amunet_quality_parameter_specification_config WHERE specification_name = 'Letra adecuada'")
n = env.cr.fetchone()[0]
print(f"'Letra adecuada' insertada/existente en {n} cartuchos")

# ── 2. Eliminar duplicado 'rasgaduras' (minúscula) sin referencias ──────────
env.cr.execute("""
    DELETE FROM amunet_quality_parameter_specification_config
    WHERE id IN (
      SELECT sc.id
      FROM amunet_quality_parameter_specification_config sc
      JOIN amunet_quality_parameter_product_rel r ON sc.product_parameter_rel_id = r.id
      JOIN product_template pt ON r.product_tmpl_id = pt.id
      WHERE (pt.default_code LIKE 'MPCAR%%' OR pt.default_code LIKE 'MPCAC%%')
        AND pt.active = true AND r.parameter_code = 'MAVI-04'
        AND sc.specification_name = 'rasgaduras'
        AND NOT EXISTS (
          SELECT 1 FROM amunet_quality_test_line_detail d
          WHERE d.specification_config_id = sc.id
        )
    )
""")
print(f"Duplicados 'rasgaduras' (minúscula) sin referencias: eliminados")

# Desactivar los que sí tienen referencias (no se pueden borrar)
env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config SET active = false, write_date = NOW()
    WHERE id IN (
      SELECT sc.id
      FROM amunet_quality_parameter_specification_config sc
      JOIN amunet_quality_parameter_product_rel r ON sc.product_parameter_rel_id = r.id
      JOIN product_template pt ON r.product_tmpl_id = pt.id
      WHERE (pt.default_code LIKE 'MPCAR%%' OR pt.default_code LIKE 'MPCAC%%')
        AND pt.active = true AND r.parameter_code = 'MAVI-04'
        AND sc.specification_name = 'rasgaduras'
        AND sc.active = true
    )
""")
print("Duplicados 'rasgaduras' con referencias: desactivados (active=false)")

print("\n✓ Script completado.")
