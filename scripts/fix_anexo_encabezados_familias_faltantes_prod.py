"""
CORRECCIÓN ENCABEZADOS DE ANEXO — Familias faltantes (producción)
==================================================================
Actualiza los encabezados de columna del Anexo en análisis existentes
que solo tienen col1='Apariencia' y las demás columnas vacías.

Familias cubiertas:
  STGO                  → ANEXO GOTERO (columnas corregidas)
  STBBM / STREX         → ANEXO BUFFER
  MPABI / MPADE / MPATR → ANEXO AGUA
  STHIS                 → ANEXO HISOPO
  STDSC                 → ANEXO DESECANTE
  MICAJ                 → ANEXO CAJA CAPLE
  STSAL                 → ANEXO SOLUCIÓN SALINA

Solo se tocan análisis donde col2_header está vacío.

Solicitado por: Diana Flores — Control de Calidad, 2026-09-28
"""

Check = env['amunet.quality.check']

FAMILIAS = [
    {
        'prefijos': ('STGOT',),
        'titulo':   'ANEXO GOTERO',
        'cols': ('Apariencia', 'Dimensiones — Punta (mm)', 'Dimensiones — Largo (mm)',
                 'Funcionalidad', '', '', '', ''),
    },
    {
        'prefijos': ('STBBM', 'STREX'),
        'titulo':   'ANEXO BUFFER',
        'cols': ('Determinación de aspectos', 'Partículas suspendidas',
                 'Migración', 'Liberación', 'Desempeño', '', '', ''),
    },
    {
        'prefijos': ('MPABI', 'MPADE', 'MPATR'),
        'titulo':   'ANEXO AGUA',
        'cols': ('Partículas', 'Color', 'Límites microbianos',
                 'Conductividad', 'pH', '', '', ''),
    },
    {
        'prefijos': ('STHIS',),
        'titulo':   'ANEXO HISOPO',
        'cols': ('Muestra', 'Apariencia — Empaque', 'Apariencia — Hisopo',
                 'Dimensiones', 'Funcionalidad prevista', 'Observaciones', '', ''),
    },
    {
        'prefijos': ('STDSC',),
        'titulo':   'ANEXO DESECANTE',
        'cols': ('Apariencia', 'Dimensiones (ancho/largo)', 'Peso inicial',
                 'Peso húmedo', 'Peso seco', 'Absorción', '', ''),
    },
    {
        'prefijos': ('MICAJ',),
        'titulo':   'ANEXO CAJA CAPLE',
        'cols': ('Apariencia', 'Ancho Interno (mm)', 'Largo Interno (mm)',
                 'Ancho Externo (mm)', 'Largo Externo (mm)', 'Alineación', 'Desempeño', ''),
    },
    {
        'prefijos': ('STSAL',),
        'titulo':   'ANEXO SOLUCIÓN SALINA',
        'cols': ('Apariencia', 'Observaciones', '', '', '', '', '', ''),
    },
]

total = 0
for familia in FAMILIAS:
    # Buscar análisis afectados por cada prefijo y reunirlos
    checks = Check.browse([])
    for prefijo in familia['prefijos']:
        checks |= Check.search([
            ('tiene_anexos', '=', True),
            ('anexo_col2_header', 'in', [False, '']),
            ('product_id.default_code', 'like', prefijo + '%'),
        ])

    if not checks:
        print(f"  {familia['prefijos']}: sin análisis que actualizar")
        continue

    c1, c2, c3, c4, c5, c6, c7, c8 = familia['cols']
    vals = {
        'anexo_titulo':      familia['titulo'],
        'anexo_col1_header': c1,
        'anexo_col2_header': c2,
        'anexo_col3_header': c3,
        'anexo_col4_header': c4,
        'anexo_col5_header': c5,
        'anexo_col6_header': c6,
        'anexo_col7_header': c7,
        'anexo_col8_header': c8,
    }

    print(f"\n  {familia['prefijos']} — {len(checks)} análisis:")
    for c in checks:
        print(f"    id={c.id}  {c.product_id.default_code}  estado={c.state}")
    checks.write(vals)
    total += len(checks)

env.cr.commit()
print(f"\n✓ {total} análisis actualizados. Las columnas ya aparecerán en el reporte PDF.")
