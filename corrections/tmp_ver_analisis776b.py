"""
Ver análisis 776 y sus líneas de detalle.
"""
QCheck = env['amunet.quality.check']
Detail = env['amunet.quality.test.line.detail']

c = QCheck.browse(776)
print(f"Análisis: {c.name} | {c.product_id.default_code} | estado: {c.state}")
print(f"Líneas: {len(c.test_line_ids)}")
for line in c.test_line_ids:
    print(f"\nLínea [{line.id}] {line.parameter_id.code} — {line.name} | verdict={line.verdict}")
    for det in line.detail_line_ids:
        # Campos disponibles
        fields_disp = [f for f in det._fields if 'result' in f or 'value' in f or 'display' in f]
        crit = det.acceptance_criteria or '-'
        print(f"  det [{det.id}] '{det.name}' | criterio: '{crit}' | tipo: {det.evaluation_type}")
