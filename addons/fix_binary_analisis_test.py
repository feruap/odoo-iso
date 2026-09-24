"""
CORRECCIÓN: binary_option_pass/fail vacíos en renglones de TODOS los análisis (producción)
============================================================================================
El fix anterior corrigió la configuración de productos, pero los análisis ya creados
guardan su propia copia del texto. Este script copia las opciones desde la configuración
vigente a todos los renglones vacíos, en cualquier estado del análisis.

Excluido: detail_id=3205 (SPHMC04 "Tiempo de migración en 4 cm de membrana") — la
          configuración también está vacía; requiere criterio de Diana.

Solicitado por: Diana Flores — Control de Calidad, 2026-09-23
"""

cr = env.cr

# Corregir usando las opciones de la config vigente
# JOIN: detail → test_line (para obtener parameter code) → check → product → config
cr.execute("""
UPDATE amunet_quality_test_line_detail tld
SET binary_option_pass = cfg.binary_option_pass,
    binary_option_fail  = cfg.binary_option_fail
FROM amunet_quality_test_line tl,
     amunet_quality_check qc,
     product_product pp,
     product_template pt,
     amunet_quality_parameter_product_rel rel,
     amunet_quality_parameter_specification_config cfg
WHERE tld.test_line_id = tl.id
  AND tl.check_id = qc.id
  AND qc.product_id = pp.id
  AND pp.product_tmpl_id = pt.id
  AND rel.product_tmpl_id = pt.id
  AND rel.parameter_code = tl.code
  AND cfg.product_parameter_rel_id = rel.id
  AND cfg.specification_name = tld.name
  AND tld.evaluation_type = 'binary_selection'
  AND (tld.binary_option_pass IS NULL OR tld.binary_option_pass = ''
    OR tld.binary_option_fail IS NULL OR tld.binary_option_fail = '')
  AND cfg.active = true
  AND cfg.binary_option_pass IS NOT NULL AND cfg.binary_option_pass != ''
  AND cfg.binary_option_fail IS NOT NULL AND cfg.binary_option_fail != ''
  AND tld.id != 3205
""")

corregidos = cr.rowcount
print(f"Renglones corregidos: {corregidos}")

env.cr.commit()

# Verificar cuántos siguen vacíos
cr.execute("""
SELECT qc.id, qc.state, pt.default_code, tld.name, tld.id as detail_id
FROM amunet_quality_test_line_detail tld
JOIN amunet_quality_test_line tl ON tld.test_line_id = tl.id
JOIN amunet_quality_check qc ON tl.check_id = qc.id
JOIN product_product pp ON qc.product_id = pp.id
JOIN product_template pt ON pp.product_tmpl_id = pt.id
WHERE tld.evaluation_type = 'binary_selection'
  AND (tld.binary_option_pass IS NULL OR tld.binary_option_pass = ''
    OR tld.binary_option_fail IS NULL OR tld.binary_option_fail = '')
ORDER BY qc.id, tld.name
""")
pendientes = cr.fetchall()
if pendientes:
    print(f"\nAún vacíos ({len(pendientes)}):")
    for row in pendientes:
        print(f"  análisis {row[0]} ({row[1]}) {row[2]}: {row[3]} (detail {row[4]})")
else:
    print("\n✓ No quedan renglones de selección binaria vacíos en ningún análisis.")

# Verificar análisis 911
cr.execute("""
SELECT tld.name, tld.binary_option_pass, tld.binary_option_fail
FROM amunet_quality_test_line_detail tld
JOIN amunet_quality_test_line tl ON tld.test_line_id = tl.id
WHERE tl.check_id = 911
  AND tld.evaluation_type = 'binary_selection'
ORDER BY tld.name
""")
print("\nAnálisis 911 — selección binaria:")
for row in cr.fetchall():
    print(f"  {row[0]}: '{row[1]}' / '{row[2]}'")
