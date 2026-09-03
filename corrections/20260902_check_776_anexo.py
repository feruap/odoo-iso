"""Ver configuración del anexo en análisis 776."""
QCheck = env['amunet.quality.check']
check = QCheck.browse(776)
print(f"Producto: {check.product_id.default_code} — {check.product_id.name}")
print(f"tiene_anexos: {check.tiene_anexos}")
print(f"anexo_titulo: {repr(check.anexo_titulo)}")
print(f"col1: {repr(check.anexo_col1_header)}")
print(f"col2: {repr(check.anexo_col2_header)}")
print(f"col3: {repr(check.anexo_col3_header)}")
print(f"col4: {repr(check.anexo_col4_header)}")
print(f"col5: {repr(check.anexo_col5_header)}")
print(f"col6: {repr(check.anexo_col6_header)}")
print(f"col7: {repr(check.anexo_col7_header)}")
print(f"col8: {repr(check.anexo_col8_header)}")
print(f"Líneas de anexo: {len(check.anexo_line_ids)}")
for line in check.anexo_line_ids[:3]:
    print(f"  muestra={repr(line.muestra)} col1={repr(line.col1)} col2={repr(line.col2)} col3={repr(line.col3)}")
