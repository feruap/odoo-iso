"""
Ver análisis 776 y sus líneas de detalle de MAVI-11 y VAMA-023.
"""
QCheck = env['amunet.quality.check']
c = QCheck.browse(776)
print(f"Análisis: {c.name} | producto: {c.product_id.default_code} — {c.product_id.name} | estado: {c.state}")
print()
for line in c.test_line_ids:
    print(f"Línea [{line.id}] {line.parameter_id.code} — {line.name} | verdict={line.verdict}")
    for det in line.detail_line_ids:
        print(f"  det [{det.id}] '{det.name}' | criterio: '{det.acceptance_criteria}' | tipo: {det.evaluation_type} | resultado: '{det.result_value or det.result_display or '-'}'")
