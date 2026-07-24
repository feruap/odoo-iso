# Back-fill de encabezados del anexo en analisis EXISTENTES de cartucho, hoja
# maestra y gotero que quedaron con "ANEXO GENERAL" (encabezados en blanco).
# Aplica la logica del codigo (_auto_enable_anexo) para dejarlos con sus
# encabezados por tipo, IGUAL que staging. NO toca datos capturados (anexo_line_ids)
# ni los productos "otros" (que correctamente quedan genericos). Solicitado por
# Fernando 2026-07-22 (diferencia detectada staging vs Main).
PREFIXES = ('MPCAR', 'MPCAC', 'MPCAG', 'SPHMC', 'SPHMT', 'STGO')
Check = env['amunet.quality.check'].sudo()

todos = Check.search([])
target = todos.filtered(
    lambda c: c.product_id.default_code
    and c.product_id.default_code.upper().startswith(PREFIXES)
    and not (c.anexo_col2_header or '').strip()
)
print('Analisis a rellenar (cartucho/hoja/gotero con encabezado en blanco):', len(target))

for c in target:
    c._auto_enable_anexo()

env.cr.commit()

# Reporte del resultado
env.cr.execute("""
    SELECT COALESCE(NULLIF(anexo_titulo,''),'(vacio)') AS titulo, count(*)
    FROM amunet_quality_check
    GROUP BY 1 ORDER BY 2 DESC
""")
print('DESPUES - analisis por titulo de anexo:')
for row in env.cr.fetchall():
    print('  ', row)
print('LISTO')
