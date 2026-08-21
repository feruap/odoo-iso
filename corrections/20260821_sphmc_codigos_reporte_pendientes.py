"""
Asigna RASP-001 / CERSP-001 v4 (sustituye v3) a las 7 hojas maestras
que tenían parámetros configurados pero sin código de reporte:
  SPHMC77 — Transglutaminasa IgA (Anti-tTG)
  SPHMC78 — HPV E7
  SPHMC80 — ToRCH Herpes 1/2 IgG/IgM
  SPHMC85 — Dengue IgG/IgM CM
  SPHMC86 — ZIKA IgG/IgM CM
  SPHMC87 — CHIKUNGUNYA IgG CM
  SPHMC88 — CHIKUNGUNYA IgM CM

Autorizado por: Diana Flores (s.controldecalidad@amunet.com.mx)
Fecha: 2026-08-21
"""

CODIGOS = ['SPHMC77', 'SPHMC78', 'SPHMC80', 'SPHMC85', 'SPHMC86', 'SPHMC87', 'SPHMC88']

for codigo in CODIGOS:
    tmpl = env['product.template'].with_context(active_test=False).search(
        [('default_code', '=', codigo)], limit=1)
    if not tmpl:
        print(f"⚠️  {codigo} no encontrado")
        continue
    tmpl.sudo().write({
        'report_document_code':        'RASP-001',
        'report_version':              4,
        'report_replaces_version':     3,
        'certificate_document_code':   'CERSP-001',
        'certificate_version':         4,
        'certificate_replaces_version': 3,
    })
    print(f"✅ {codigo} — RASP-001 v4/3 y CERSP-001 v4/3")

env.cr.commit()
print("\nListo — 7 hojas maestras actualizadas.")
