"""
Corrección URGENTE: MAVI-07 en análisis abiertos de STBPR01-04 en producción.

Problema:
  - Detalles de "Muestra negativa" duplicados (tipo mavi_07 + vama_multi_check)
  - Tipo incorrecto: mavi_07 y vama_multi_check no muestran semáforo pass/fail
  - Tipo correcto: mavi_07_ternary (igual que STBPR03 de referencia)
  - Algunos análisis carecen de "Muestra positiva"
  - Spec configs de STBPR02/04 con active=NULL que impiden cerrar análisis

Pasos:
  1. Eliminar "Muestra negativa" vama_multi_check duplicada donde ya existe mavi_07
  2. Corregir todos los "Muestra negativa" → mavi_07_ternary + criterio correcto
  3. Corregir todos los "Muestra positiva" → mavi_07_ternary + criterio correcto
  4. Insertar "Muestra positiva" donde falta (análisis 468, 469, 470)

NOTA: El script anterior (20260828_calidad_buffers_qc_prod.py) ya creó specs activas
nuevas para STBPR04 (88702/88703) y STBPR02 Positiva (88707). Las inactivas viejas
(80778/80810/80811) se dejan como están para evitar duplicados activos.

Confirmado por Diana Flores, 2026-08-28.
Idempotente — seguro de correr más de una vez.
"""

# ── 1. Eliminar "Muestra negativa" vama_multi_check duplicada ────────────────────
env.cr.execute("""
    DELETE FROM amunet_quality_test_line_detail
    WHERE id IN (
        SELECT td.id
        FROM amunet_quality_test_line_detail td
        JOIN amunet_quality_test_line tl ON tl.id=td.test_line_id
        JOIN amunet_quality_check_parameter p ON p.id=tl.parameter_id AND p.code='MAVI-07'
        JOIN amunet_quality_check qc ON qc.id=tl.check_id
        JOIN product_product pp ON pp.id=qc.product_id
        JOIN product_template pt ON pt.id=pp.product_tmpl_id
        WHERE td.name='Muestra negativa'
          AND td.evaluation_type='vama_multi_check'
          AND pt.default_code IN ('STBPR01','STBPR02','STBPR03','STBPR04')
          AND qc.state NOT IN ('done','cancel')
          AND EXISTS (
              SELECT 1 FROM amunet_quality_test_line_detail td2
              WHERE td2.test_line_id=td.test_line_id
                AND td2.name='Muestra negativa'
                AND td2.evaluation_type='mavi_07'
          )
    )
""")
print(f"Detalles duplicados eliminados: {env.cr.rowcount}")

# ── 3. Corregir "Muestra negativa" → mavi_07_ternary ────────────────────────────
env.cr.execute("""
    UPDATE amunet_quality_test_line_detail td
    SET evaluation_type='mavi_07_ternary',
        acceptance_criteria='#5',
        sequence=20,
        specification_id=628,
        specification_config_id=(
            SELECT sc.id FROM amunet_quality_parameter_specification_config sc
            WHERE sc.product_parameter_rel_id=tl.parameter_rel_id
              AND sc.specification_id=628 AND sc.active=true LIMIT 1
        ),
        write_date=NOW()
    FROM amunet_quality_test_line tl
    JOIN amunet_quality_check qc ON qc.id=tl.check_id
    JOIN amunet_quality_check_parameter p ON p.id=tl.parameter_id AND p.code='MAVI-07'
    JOIN product_product pp ON pp.id=qc.product_id
    JOIN product_template pt ON pt.id=pp.product_tmpl_id
    WHERE td.test_line_id=tl.id
      AND td.name='Muestra negativa'
      AND pt.default_code IN ('STBPR01','STBPR02','STBPR03','STBPR04')
      AND qc.state NOT IN ('done','cancel')
""")
print(f"'Muestra negativa' corregidas: {env.cr.rowcount}")

# ── 4. Corregir "Muestra positiva" → mavi_07_ternary ────────────────────────────
env.cr.execute("""
    UPDATE amunet_quality_test_line_detail td
    SET evaluation_type='mavi_07_ternary',
        acceptance_criteria='#1, #2, #3 y #4',
        sequence=10,
        specification_id=629,
        specification_config_id=(
            SELECT sc.id FROM amunet_quality_parameter_specification_config sc
            WHERE sc.product_parameter_rel_id=tl.parameter_rel_id
              AND sc.specification_id=629 AND sc.active=true LIMIT 1
        ),
        write_date=NOW()
    FROM amunet_quality_test_line tl
    JOIN amunet_quality_check qc ON qc.id=tl.check_id
    JOIN amunet_quality_check_parameter p ON p.id=tl.parameter_id AND p.code='MAVI-07'
    JOIN product_product pp ON pp.id=qc.product_id
    JOIN product_template pt ON pt.id=pp.product_tmpl_id
    WHERE td.test_line_id=tl.id
      AND td.name='Muestra positiva'
      AND pt.default_code IN ('STBPR01','STBPR02','STBPR03','STBPR04')
      AND qc.state NOT IN ('done','cancel')
""")
print(f"'Muestra positiva' corregidas: {env.cr.rowcount}")

# ── 5. Insertar "Muestra positiva" donde falta ───────────────────────────────────
env.cr.execute("""
    INSERT INTO amunet_quality_test_line_detail
      (test_line_id, check_id, name, specification_id, specification_config_id,
       evaluation_type, acceptance_criteria, sequence, create_uid, write_uid, create_date, write_date)
    SELECT tl.id, tl.check_id, 'Muestra positiva', 629,
        (SELECT sc.id FROM amunet_quality_parameter_specification_config sc
         WHERE sc.product_parameter_rel_id=tl.parameter_rel_id
           AND sc.specification_id=629 AND sc.active=true LIMIT 1),
        'mavi_07_ternary', '#1, #2, #3 y #4', 10,
        2, 2, NOW(), NOW()
    FROM amunet_quality_test_line tl
    JOIN amunet_quality_check qc ON qc.id=tl.check_id
    JOIN amunet_quality_check_parameter p ON p.id=tl.parameter_id AND p.code='MAVI-07'
    JOIN product_product pp ON pp.id=qc.product_id
    JOIN product_template pt ON pt.id=pp.product_tmpl_id
    WHERE pt.default_code IN ('STBPR01','STBPR02','STBPR03','STBPR04')
      AND qc.state NOT IN ('done','cancel')
      AND NOT EXISTS (
          SELECT 1 FROM amunet_quality_test_line_detail td2
          WHERE td2.test_line_id=tl.id AND td2.name='Muestra positiva'
      )
""")
print(f"'Muestra positiva' insertadas: {env.cr.rowcount}")

# ── 6. Corregir acceptance_criteria en spec configs activas ─────────────────────
env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config sc
    SET acceptance_criteria = CASE sc.specification_name
          WHEN 'Muestra positiva' THEN '#1, #2, #3 y #4'
          WHEN 'Muestra negativa' THEN '#5'
        END,
        write_date = NOW()
    FROM amunet_quality_parameter_product_rel r
    JOIN product_template pt ON r.product_tmpl_id=pt.id
    WHERE sc.product_parameter_rel_id=r.id
      AND r.parameter_code='MAVI-07'
      AND pt.default_code IN ('STBPR01','STBPR02','STBPR03','STBPR04')
      AND sc.active=true
      AND sc.specification_name IN ('Muestra positiva','Muestra negativa')
""")
print(f"Spec configs MAVI-07 acceptance_criteria corregidas: {env.cr.rowcount}")

# ── 7. Configurar ANEXO BUFFER en análisis abiertos ─────────────────────────────
env.cr.execute("""
    UPDATE amunet_quality_check
    SET tiene_anexos      = true,
        is_material_con_anexo = true,
        anexo_titulo      = 'ANEXO BUFFER',
        anexo_col1_header = 'Partículas suspendidas',
        anexo_col2_header = 'Liberación de conjugado',
        anexo_col3_header = 'Migración de conjugado',
        anexo_col4_header = 'Desempeño',
        anexo_col5_header = '',
        anexo_col6_header = '',
        anexo_col7_header = '',
        write_date = NOW()
    WHERE id IN (
        SELECT qc.id FROM amunet_quality_check qc
        JOIN product_product pp ON pp.id=qc.product_id
        JOIN product_template pt ON pt.id=pp.product_tmpl_id
        WHERE pt.default_code IN ('STBPR01','STBPR02','STBPR03','STBPR04')
          AND qc.state NOT IN ('done','cancel')
    )
""")
print(f"ANEXO BUFFER configurado en análisis abiertos: {env.cr.rowcount}")

# ── Verificación final ────────────────────────────────────────────────────────────
env.cr.execute("""
    SELECT qc.id, pt.default_code, COUNT(td.id) AS detalles,
           STRING_AGG(td.evaluation_type, ', ' ORDER BY td.sequence) AS tipos
    FROM amunet_quality_check qc
    JOIN product_product pp ON pp.id=qc.product_id
    JOIN product_template pt ON pt.id=pp.product_tmpl_id
    JOIN amunet_quality_test_line tl ON tl.check_id=qc.id
    JOIN amunet_quality_check_parameter p ON p.id=tl.parameter_id AND p.code='MAVI-07'
    JOIN amunet_quality_test_line_detail td ON td.test_line_id=tl.id
    WHERE pt.default_code IN ('STBPR01','STBPR02','STBPR03','STBPR04')
      AND qc.state NOT IN ('done','cancel')
    GROUP BY qc.id, pt.default_code
    ORDER BY qc.id
""")
rows = env.cr.fetchall()
for r in rows:
    ok = "✓" if r[2] == 2 and r[3] == 'mavi_07_ternary, mavi_07_ternary' else "✗"
    print(f"  {ok} análisis {r[0]} {r[1]}: {r[2]} detalles | tipos: {r[3]}")

print("\n✓ Script completado.")
