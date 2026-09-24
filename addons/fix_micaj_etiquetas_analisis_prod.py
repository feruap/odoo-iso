"""
CORRECCIÓN: etiquetas Ancho/Largo invertidas en líneas de análisis MICAJ (producción)
=======================================================================================
Los análisis de MICAJ01-14 creados antes de corregir la configuración tienen el nombre
"Ancho" asignado al rango 195-205 (debería decir "Largo") y "Largo" al rango 105-115
(debería decir "Ancho"). El certificado muestra "Ancho: 200" y "Largo: 110" — al revés.

El análisis más reciente (MICAJ01 id=890, hoy) ya nació correcto.

Corrección: intercambiar name='Ancho'↔'Largo' SOLO en las líneas donde el rango
            delata que la etiqueta está invertida (Ancho>=190 o Largo<=120).

Afecta detail_ids: 2056-2057, 2067-2068, 2078-2079, 2089-2090, 2100-2101,
                   2111-2112, 2122-2123, 2155-2156, 2166-2167, 2177-2178,
                   2188-2189, 2199-2200

Solicitado por: Diana Flores — Control de Calidad, 2026-09-23
"""

cr = env.cr

# Corregir: donde name='Ancho' y rango>=190 → cambiar a 'Largo'
cr.execute("""
    UPDATE amunet_quality_test_line_detail
    SET name = 'Largo'
    WHERE name = 'Ancho' AND min_value >= 190
      AND id IN (2056,2067,2078,2089,2100,2111,2122,2155,2166,2177,2188,2199)
""")
print(f"Ancho→Largo: {cr.rowcount} filas")

# Corregir: donde name='Largo' y rango<=120 → cambiar a 'Ancho'
cr.execute("""
    UPDATE amunet_quality_test_line_detail
    SET name = 'Ancho'
    WHERE name = 'Largo' AND min_value <= 120 AND max_value <= 120
      AND id IN (2057,2068,2079,2090,2101,2112,2123,2156,2167,2178,2189,2200)
""")
print(f"Largo→Ancho: {cr.rowcount} filas")

env.cr.commit()
print("\n✓ Etiquetas corregidas en análisis MICAJ.")

# Verificar
cr.execute("""
    SELECT qc.analysis_number, pt.default_code, tld.name, tld.min_value, tld.max_value
    FROM amunet_quality_test_line_detail tld
    JOIN amunet_quality_test_line tl ON tld.test_line_id = tl.id
    JOIN amunet_quality_check qc ON tl.check_id = qc.id
    JOIN product_product pp ON qc.product_id = pp.id
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE tld.id IN (2056,2057,2155,2156,2199,2200)
    ORDER BY pt.default_code, tld.name
""")
for row in cr.fetchall():
    print(f"  {row[1]} ({row[0] or 'sin folio'}): {row[2]} = {row[3]}-{row[4]}")
