"""Corregir encabezados del anexo en análisis 776 (STHIE01 Hielera chica)."""
QCheck = env['amunet.quality.check']
check = QCheck.browse(776)

# Ver col5 y col6 en las líneas
for line in check.anexo_line_ids[:3]:
    print(f"  m={line.muestra} col5={repr(line.col5)} col6={repr(line.col6)} col7={repr(line.col7)}")

# Orden de columnas según MAVI-11 del análisis:
# col1=Apariencia, col2=Largo, col3=Alto, col4=Ancho, col5=Grosor, col6=Cap.cierre
check.write({
    'anexo_titulo':      'ANEXO HIELERA CHICA',
    'anexo_col1_header': 'Apariencia',
    'anexo_col2_header': 'Largo (cm)',
    'anexo_col3_header': 'Alto (cm)',
    'anexo_col4_header': 'Ancho (cm)',
    'anexo_col5_header': 'Grosor (cm)',
    'anexo_col6_header': '',
    'anexo_col7_header': '',
    'anexo_col8_header': '',
})
print(f"Encabezados actualizados.")
print(f"col1={repr(check.anexo_col1_header)}")
print(f"col2={repr(check.anexo_col2_header)}")
print(f"col3={repr(check.anexo_col3_header)}")
print(f"col4={repr(check.anexo_col4_header)}")
print(f"col5={repr(check.anexo_col5_header)}")
env.cr.commit()
print("✓ Listo.")
