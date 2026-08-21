"""
Asigna códigos de documento y versiones al producto SPHMC79 (Hoja Maestra CARBA 5en1):
  report_document_code      = RASP-001   versión 4  (sustituye a la 3)
  certificate_document_code = CERSP-001  versión 4  (sustituye a la 3)

Mismo patrón que SPHMC18 y SPHMC22 (hojas maestras cualitativas de referencia).

Autorizado por: Diana Flores (s.controldecalidad@amunet.com.mx)
Fecha: 2026-08-21
"""

tmpl = env['product.template'].with_context(active_test=False).search(
    [('default_code', '=', 'SPHMC79')], limit=1)

if not tmpl:
    print("ERROR: SPHMC79 no encontrado")
    raise SystemExit(1)

tmpl.sudo().write({
    'report_document_code':       'RASP-001',
    'report_version':             4,
    'report_replaces_version':    3,
    'certificate_document_code':  'CERSP-001',
    'certificate_version':        4,
    'certificate_replaces_version': 3,
})

env.cr.commit()
print("✅ SPHMC79 — RASP-001 v4/3 y CERSP-001 v4/3 configurados correctamente.")
