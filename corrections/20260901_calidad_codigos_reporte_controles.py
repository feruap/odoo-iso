"""
Códigos de reporte, certificado y referencias para controles de calidad.

Estructura clave conjunta / clave individual (igual que cartuchos):
  - STCOP01 (conjunta)  →  STCPL01-16 (individuales positivos)
      Reporte:      RAST-038  rev.04  Ago.2025
      Certificado:  CERST-038 rev.04
      Referencias:  ESPST-038 · TAST-038 · PNOCC-002

  - STCON01 (conjunta)  →  STCNL01 (único control negativo actual)
      Reporte:      RAST-039  rev.04  Ago.2025
      Certificado:  CERST-039 rev.04
      Referencias:  ESPST-039 · TAST-039

Confirmado por Diana Flores, 2026-09-01.
Idempotente — seguro de correr más de una vez.
"""

REFS_POSITIVO = ('- ESPST-038\n'
                 '- Técnica de análisis TAST-038\n'
                 '- Inspección de Insumos PNOCC-002\n'
                 '- Método de muestreo de acuerdo a la Norma ANSI/ASQ Z1.4 PNOCC-005')
REFS_NEGATIVO = ('- ESPST-039\n'
                 '- Técnica de análisis TAST-039\n'
                 '- Inspección de Insumos PNOCC-002\n'
                 '- Método de muestreo de acuerdo a la Norma ANSI/ASQ Z1.4 PNOCC-005')

POSITIVOS = [
    'STCOP01',
    'STCPL01', 'STCPL02', 'STCPL03', 'STCPL04',
    'STCPL05', 'STCPL06', 'STCPL07', 'STCPL08',
    'STCPL09', 'STCPL10', 'STCPL11', 'STCPL12',
    'STCPL13', 'STCPL14', 'STCPL15', 'STCPL16',
]

NEGATIVOS = ['STCON01', 'STCNL01', 'SPCNL04']

# ── Controles positivos ───────────────────────────────────────────────────────
print("── Controles positivos (RAST-038 / CERST-038) ──")
for codigo in POSITIVOS:
    env.cr.execute("""
        UPDATE product_template SET
            report_document_code       = 'RAST-038',
            report_version             = 4,
            report_effective_date      = '2025-08-01',
            certificate_document_code  = 'CERST-038',
            certificate_version        = 4,
            certificate_effective_date = '2025-08-01',
            report_references          = %s
        WHERE default_code = %s
    """, (REFS_POSITIVO, codigo))
    print(f"  {codigo}: {env.cr.rowcount} registro(s) actualizado(s)")

# ── Controles negativos ───────────────────────────────────────────────────────
print("\n── Controles negativos (RAST-039 / CERST-039) ──")
for codigo in NEGATIVOS:
    env.cr.execute("""
        UPDATE product_template SET
            report_document_code       = 'RAST-039',
            report_version             = 4,
            report_effective_date      = '2025-08-01',
            certificate_document_code  = 'CERST-039',
            certificate_version        = 4,
            certificate_effective_date = '2025-08-01',
            report_references          = %s
        WHERE default_code = %s
    """, (REFS_NEGATIVO, codigo))
    print(f"  {codigo}: {env.cr.rowcount} registro(s) actualizado(s)")

# ── ANEXO: agregar Desempeño entre Migración y Observación ───────────────────
print("\n── Actualizando ANEXO con columna Desempeño ──")
todos_controles = POSITIVOS + NEGATIVOS
env.cr.execute("""
    UPDATE amunet_quality_check SET
        anexo_col4_header = 'Desempeño',
        anexo_col5_header = 'Observación',
        anexo_col6_header = '',
        anexo_col7_header = '',
        anexo_col8_header = ''
    WHERE product_id IN (
        SELECT pp.id FROM product_product pp
        JOIN product_template pt ON pt.id = pp.product_tmpl_id
        WHERE pt.default_code = ANY(%s)
    )
    AND state NOT IN ('done','cancel')
    AND tiene_anexos = true
""", (todos_controles,))
print(f"  Análisis actualizados con Desempeño: {env.cr.rowcount}")

env.cr.commit()
print("\n✓ Códigos de reporte, certificado, referencias y ANEXO aplicados a controles positivos y negativos.")
