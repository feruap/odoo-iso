import base64, os

F   = env['amunet.documento.formato']
Doc = env['amunet.documento']
DIR = '/tmp/formatos_ge'

def b64(filename):
    with open(os.path.join(DIR, filename), 'rb') as f:
        return base64.b64encode(f.read()).decode()

grupos = [
    {
        'doc': 'PNOGE-003',
        'formatos': [
            {'seq': 10, 'codigo': 'F-GE-003/001', 'nombre': 'Control de cambios',
             'file': 'F-GE-003-001 CONTROL DE CAMBIOS.docx',
             'dl':   'F-GE-003-001 Control de cambios.docx'},
            {'seq': 20, 'codigo': 'F-GE-003/002', 'nombre': 'Registro anual de control de cambios',
             'file': 'F-GE-003-002 REGISTRO ANUAL DE CONTROL DE CAMBIOS.docx',
             'dl':   'F-GE-003-002 Registro anual de control de cambios.docx'},
        ],
    },
    {
        'doc': 'PNOGE-004',
        'formatos': [
            {'seq': 10, 'codigo': 'F-GE-004/001', 'nombre': 'Registro anual de desviaciones o no conformidades',
             'file': 'F-GE-004-003 REGISTRO ANUAL DE DESVIACIONES O NO CONFORMIDADES.docx',
             'dl':   'F-GE-004-001 Registro anual de desviaciones o no conformidades.docx'},
            {'seq': 20, 'codigo': 'F-GE-004/002', 'nombre': 'Reporte de desviaciones o no conformidades',
             'file': 'F-GE-004_004 Desviaciones_VER 02.docx',
             'dl':   'F-GE-004-002 Reporte de desviaciones o no conformidades.docx'},
        ],
    },
    {
        'doc': 'PNOGE-007',
        'formatos': [
            {'seq': 10, 'codigo': 'F-GE-007/001', 'nombre': 'Entrega de indumentaria',
             'file': 'F-GE-007-005 Entrega de indumentaria.docx',
             'dl':   'F-GE-007-001 Entrega de indumentaria.docx'},
            {'seq': 20, 'codigo': 'F-GE-007/002', 'nombre': 'Revisión de indumentaria',
             'file': 'F-GE-007 006 Revisión de indumentaria.docx',
             'dl':   'F-GE-007-002 Revision de indumentaria.docx'},
        ],
    },
    {
        'doc': 'PNOGE-008',
        'formatos': [
            {'seq': 10, 'codigo': 'F-GE-008/001', 'nombre': 'Flujo de material — acceso 1',
             'file': 'F-GE-008-001 Flujo de material acceso 1.docx',
             'dl':   'F-GE-008-001 Flujo de material acceso 1.docx'},
            {'seq': 20, 'codigo': 'F-GE-008/002', 'nombre': 'Flujo de material — acceso 2',
             'file': 'F-GE-008-002 Flujo de material acceso 2.docx',
             'dl':   'F-GE-008-002 Flujo de material acceso 2.docx'},
            {'seq': 30, 'codigo': 'F-GE-008/003', 'nombre': 'Flujo de personal',
             'file': 'F-GE-008-003 Flujo de personal.docx',
             'dl':   'F-GE-008-003 Flujo de personal.docx'},
            {'seq': 40, 'codigo': 'F-GE-008/004', 'nombre': 'Proceso de fabricación',
             'file': 'F-GE-008-004 Proceso de fabricación.docx',
             'dl':   'F-GE-008-004 Proceso de fabricacion.docx'},
            {'seq': 50, 'codigo': 'F-GE-008/005', 'nombre': 'Flujo de desechos',
             'file': 'F-GE-008-005 Flujo de desechos.docx',
             'dl':   'F-GE-008-005 Flujo de desechos.docx'},
            {'seq': 60, 'codigo': 'F-GE-008/006', 'nombre': 'Planos actuales',
             'file': 'F-GE-008-006 Planos actuales.docx',
             'dl':   'F-GE-008-006 Planos actuales.docx'},
        ],
    },
    {
        'doc': 'PNOGE-009',
        'formatos': [
            {'seq': 10, 'codigo': 'F-GE-009/001', 'nombre': 'Matriz de análisis de riesgos',
             'file': 'F-GE-009-005 Matriz analisis de riesgos.xlsx',
             'dl':   'F-GE-009-001 Matriz de analisis de riesgos.xlsx'},
            {'seq': 20, 'codigo': 'F-GE-009/002', 'nombre': 'Informe de análisis de riesgo AMEF',
             'file': 'F-GE-009-006 INFORME DE ANALISIS DE RIESGO AMEF.docx',
             'dl':   'F-GE-009-002 Informe de analisis de riesgo AMEF.docx'},
            {'seq': 30, 'codigo': 'F-GE-009/003', 'nombre': 'Registro de análisis de riesgos',
             'file': 'F-GE-009-007 REG ANALISIS DE RIESGOS.docx',
             'dl':   'F-GE-009-003 Registro de analisis de riesgos.docx'},
        ],
    },
]

for grupo in grupos:
    doc = Doc.search([('codigo', '=', grupo['doc'])], limit=1)
    if not doc:
        print(f'SKIP — no encontré {grupo["doc"]}')
        continue
    F.search([('documento_id', '=', doc.id)]).unlink()
    for r in grupo['formatos']:
        F.create({
            'documento_id':     doc.id,
            'sequence':         r['seq'],
            'codigo':           r['codigo'],
            'nombre':           r['nombre'],
            'archivo':          b64(r['file']),
            'archivo_filename': r['dl'],
        })
        print(f'  OK — {doc.codigo} → {r["codigo"]}')

env.cr.commit()
print('Listo: formatos GENERALES cargados')
