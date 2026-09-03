"""Verificar result_display en la tabla de DETALLES para análisis 787."""
env.cr.execute("""
    SELECT d.id, d.evaluation_type, d.result_display, d.multi_check_results_json
    FROM amunet_quality_test_line_detail d
    JOIN amunet_quality_test_line l ON l.id = d.test_line_id
    WHERE l.check_id = 787
      AND d.evaluation_type = 'vama_multi_check'
    LIMIT 5
""")
rows = env.cr.fetchall()
print("=== Detalles vama_multi_check en análisis 787 ===")
for r in rows:
    print(f"  detail id={r[0]} eval={r[1]} result_display={repr(r[2])} json={r[3][:60] if r[3] else None}")

# También verificar que la columna result_display existe en la tabla detail
env.cr.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_name = 'amunet_quality_test_line_detail'
      AND column_name = 'result_display'
""")
col = env.cr.fetchone()
print(f"\nColumna result_display en amunet_quality_test_line_detail: {'SÍ EXISTE' if col else 'NO EXISTE'}")
