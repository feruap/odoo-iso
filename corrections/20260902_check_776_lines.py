"""Ver líneas y datos del análisis 776 para entender las columnas del anexo."""
QCheck = env['amunet.quality.check']
check = QCheck.browse(776)
print("=== Líneas de prueba ===")
for line in check.test_line_ids:
    print(f"  line {line.id}: {line.code} — {line.name} | verdict={line.verdict}")
    for d in line.detail_line_ids:
        print(f"    detail {d.id}: {repr(d.name)} | eval={d.evaluation_type} | crit={repr(d.acceptance_criteria)}")

print("\n=== Primeras 3 líneas del anexo ===")
for line in check.anexo_line_ids[:3]:
    print(f"  m={line.muestra} col1={repr(line.col1)} col2={repr(line.col2)} col3={repr(line.col3)} col4={repr(line.col4)} col5={repr(line.col5)}")
