"""Fix temporal: result_display de MAVI-20 en análisis activos."""
import json as _json

# Buscar por SQL — evita dependencia de campos que pueden diferir entre versiones
env.cr.execute("""
    SELECT d.id, d.multi_check_results_json, d.text_phrase_mapping,
           qc.name as check_name
    FROM amunet_quality_test_line_detail d
    JOIN amunet_quality_test_line l ON l.id = d.test_line_id
    JOIN amunet_quality_check qc ON qc.id = l.check_id
    WHERE d.evaluation_type = 'vama_multi_check'
      AND qc.state NOT IN ('done', 'cancel')
      AND d.multi_check_results_json IS NOT NULL
      AND d.multi_check_results_json != '{}'
""")
rows = env.cr.fetchall()
print(f"Detalles vama_multi_check con datos en análisis activos: {len(rows)}")

actualizados = 0
for (det_id, raw_results, raw_mapping, check_name) in rows:
    if not raw_results or not raw_mapping:
        continue
    try:
        results = _json.loads(raw_results)
        mapping = _json.loads(raw_mapping)
    except Exception:
        continue

    positions       = mapping.get('positions', [])
    success_message = mapping.get('success_message', '')
    error_prefix    = mapping.get('error_prefix', 'No cumple:')
    # Saltar si es MAVI-07 (tiene fixed_sample_type o evaluation.rules list)
    if mapping.get('fixed_sample_type') or (
        isinstance(mapping.get('evaluation', {}).get('rules'), list)
    ):
        continue
    if not positions or not success_message:
        continue

    failed = []
    pending = False
    for i, pos in enumerate(positions):
        val = results.get(str(i), '')
        if not val:
            pending = True
            break
        if pos.get('type', 'binary') == 'binary':
            if val != pos.get('pass_value', 'A'):
                failed.append(pos.get('label', f'Pos {i+1}'))

    if pending:
        continue

    new_display = (error_prefix + ': ' + ', '.join(failed)) if failed else success_message

    env.cr.execute(
        "SELECT result_display FROM amunet_quality_test_line_detail WHERE id = %s",
        (det_id,)
    )
    current = env.cr.fetchone()[0]
    if current != new_display:
        env.cr.execute(
            "UPDATE amunet_quality_test_line_detail SET result_display = %s WHERE id = %s",
            (new_display, det_id)
        )
        actualizados += 1
        print(f"  Detail {det_id} ({check_name}): '{new_display[:70]}'")

env.cr.commit()
print(f"\n✓ {actualizados} detalles MAVI-20 actualizados.")
