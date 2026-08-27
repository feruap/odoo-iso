"""
Correcciones goteros (STGOT01–07) en producción:
1. Agrega MAVI-17 (Conteo de gotas) a los 6 goteros que no lo tienen.
2. Elimina VAMA-038 de todos los goteros (sustituido por MAVI-17).
3. Elimina las 16 specs en cero del MAVI-11 de STGOT02 y STGOT03
   (specs de plantilla genérica que no aplican al gotero).
Confirmado por Diana Flores, 2026-08-27.

Idempotente — seguro de correr más de una vez.
Correr UNA VEZ después del deploy a producción.
Nota: STGOT02 MAVI-17 ya existe en producción y fue corregido por
      el script 20260826_calidad_goteros_y_stbhe01.py.
"""

# ── 1. Agregar MAVI-17 a los goteros que no lo tienen ───────────────────────
# Valores confirmados por Diana:
#   STGOT01 Capilar:            10 µl ±5  (5–15)
#   STGOT03 Grande punta larga: 20 µl ±5  (15–25)
#   STGOT04 Gotero 25 µl:       25 µl ±5  (20–30)
#   STGOT05 Gotero 40 µl:       40 µl ±5  (35–45)
#   STGOT06 Antidoping SSP:     40 µl ±5  (35–45)
#   STGOT07 Punta capilar:      20 µl ±5  (15–25)

MAVI17_SPECS = [
    ('STGOT01', '10 µl ±5 µl',  5,  10, 15, 5),
    ('STGOT03', '20 µl ±5 µl', 15,  20, 25, 5),
    ('STGOT04', '25 µl ±5 µl', 20,  25, 30, 5),
    ('STGOT05', '40 µl ±5 µl', 35,  40, 45, 5),
    ('STGOT06', '40 µl ±5 µl', 35,  40, 45, 5),
    ('STGOT07', '20 µl ±5 µl', 15,  20, 25, 5),
]

for code, criterio, vmin, nominal, vmax, tol in MAVI17_SPECS:
    # Crear rel si no existe
    env.cr.execute("""
        INSERT INTO amunet_quality_parameter_product_rel
          (product_tmpl_id, parameter_id, parameter_code, create_uid, write_uid, create_date, write_date)
        SELECT pt.id,
               (SELECT r2.parameter_id FROM amunet_quality_parameter_product_rel r2
                JOIN product_template pt2 ON r2.product_tmpl_id = pt2.id
                WHERE pt2.default_code = 'STGOT02' AND r2.parameter_code = 'MAVI-17' LIMIT 1),
               'MAVI-17', 1, 1, NOW(), NOW()
        FROM product_template pt
        WHERE pt.default_code = %s
          AND NOT EXISTS (
            SELECT 1 FROM amunet_quality_parameter_product_rel r3
            JOIN product_template pt3 ON r3.product_tmpl_id = pt3.id
            WHERE pt3.default_code = %s AND r3.parameter_code = 'MAVI-17'
          )
    """, [code, code])

    # Crear spec si no existe
    env.cr.execute("""
        INSERT INTO amunet_quality_parameter_specification_config
          (product_parameter_rel_id, specification_id, specification_name,
           evaluation_type, acceptance_criteria,
           min_value, nominal_value, max_value, tolerance,
           active, create_uid, write_uid, create_date, write_date)
        SELECT r.id,
               (SELECT sc2.specification_id
                FROM amunet_quality_parameter_specification_config sc2
                JOIN amunet_quality_parameter_product_rel r2 ON sc2.product_parameter_rel_id = r2.id
                JOIN product_template pt2 ON r2.product_tmpl_id = pt2.id
                WHERE pt2.default_code = 'STGOT02' AND r2.parameter_code = 'MAVI-17' LIMIT 1),
               'Conteo de gotas', 'numeric_range', %s,
               %s, %s, %s, %s,
               true, 1, 1, NOW(), NOW()
        FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON r.product_tmpl_id = pt.id
        WHERE pt.default_code = %s AND r.parameter_code = 'MAVI-17'
          AND NOT EXISTS (
            SELECT 1 FROM amunet_quality_parameter_specification_config sc3
            WHERE sc3.product_parameter_rel_id = r.id
          )
    """, [criterio, vmin, nominal, vmax, tol, code])

    print(f"{code} MAVI-17: Conteo de gotas {criterio} → OK")

# ── 2. Eliminar VAMA-038 de todos los goteros ────────────────────────────────
env.cr.execute("""
    DELETE FROM amunet_quality_parameter_specification_config
    WHERE product_parameter_rel_id IN (
        SELECT r.id FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON r.product_tmpl_id = pt.id
        WHERE pt.default_code LIKE 'STGOT%%' AND r.parameter_code = 'VAMA-038'
    )
    AND NOT EXISTS (
        SELECT 1 FROM amunet_quality_test_line_detail d
        WHERE d.specification_config_id = amunet_quality_parameter_specification_config.id
    )
""")
env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config SET active = false, write_date = NOW()
    WHERE product_parameter_rel_id IN (
        SELECT r.id FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON r.product_tmpl_id = pt.id
        WHERE pt.default_code LIKE 'STGOT%%' AND r.parameter_code = 'VAMA-038'
    ) AND active = true
""")
env.cr.execute("""
    DELETE FROM amunet_quality_parameter_product_rel
    WHERE parameter_code = 'VAMA-038'
      AND product_tmpl_id IN (
          SELECT id FROM product_template WHERE default_code LIKE 'STGOT%%'
      )
      AND NOT EXISTS (
          SELECT 1 FROM amunet_quality_parameter_specification_config sc
          WHERE sc.product_parameter_rel_id = amunet_quality_parameter_product_rel.id
      )
""")
print("VAMA-038 eliminado de todos los goteros")

# ── 3. Eliminar specs en cero de MAVI-11 en STGOT02 y STGOT03 ───────────────
env.cr.execute("""
    DELETE FROM amunet_quality_parameter_specification_config
    WHERE product_parameter_rel_id IN (
        SELECT r.id FROM amunet_quality_parameter_product_rel r
        JOIN product_template pt ON r.product_tmpl_id = pt.id
        WHERE pt.default_code IN ('STGOT02','STGOT03') AND r.parameter_code = 'MAVI-11'
    )
    AND COALESCE(min_value, 0) = 0
    AND COALESCE(max_value, 0) = 0
    AND COALESCE(nominal_value, 0) = 0
    AND NOT EXISTS (
        SELECT 1 FROM amunet_quality_test_line_detail d
        WHERE d.specification_config_id = amunet_quality_parameter_specification_config.id
    )
""")
print("STGOT02/03 MAVI-11: specs en cero (plantilla) eliminadas")

print("\n✓ Script completado.")
