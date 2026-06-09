import base64, os

F   = env['amunet.documento.formato']
Doc = env['amunet.documento']
DIR = '/tmp/formatos_pr'

def b64(filename):
    with open(os.path.join(DIR, filename), 'rb') as f:
        return base64.b64encode(f.read()).decode()

grupos = [
    {
        'doc': 'PNOPR-001',
        'formatos': [
            {'seq': 10, 'codigo': 'F-PR-001/001', 'nombre': 'Despeje de línea',
             'file': 'F-PR-001-001 DESPEJE DE LÍNEA.docx',
             'dl':   'F-PR-001-001 Despeje de linea.docx'},
        ],
    },
    {
        'doc': 'PNOPR-003',
        'formatos': [
            {'seq': 10, 'codigo': 'F-PR-003/001', 'nombre': 'Rotación de sanitizantes',
             'file': 'F-PR-003-002 Rotación de sanitizantes.docx',
             'dl':   'F-PR-003-001 Rotacion de sanitizantes.docx'},
            {'seq': 20, 'codigo': 'F-PR-003/002', 'nombre': 'Limpieza del área de producción',
             'file': 'F-PR-003-003 LIMPIEZA DE PRODUCCIÓN V02.docx',
             'dl':   'F-PR-003-002 Limpieza del area de produccion.docx'},
        ],
    },
    {
        'doc': 'PNOPR-005',
        'formatos': [
            {'seq': 10, 'codigo': 'F-PR-005/001', 'nombre': 'Programa anual de mantenimiento preventivo',
             'file': 'F-PR-005-004 Programa anual mnto preventivo 2024.docx',
             'dl':   'F-PR-005-001 Programa anual de mantenimiento preventivo.docx'},
        ],
    },
    {
        'doc': 'PNOPR-006',
        'formatos': [
            {'seq': 10, 'codigo': 'F-PR-006/001', 'nombre': 'Soluciones generales',
             'file': 'F-PR-006-005 Soluciones Generales.docx',
             'dl':   'F-PR-006-001 Soluciones generales.docx'},
            {'seq': 20, 'codigo': 'F-PR-006/002', 'nombre': 'Soluciones de AB y PRO',
             'file': 'F-PR-006-006 Soluciones de AB y PRO.docx',
             'dl':   'F-PR-006-002 Soluciones de AB y PRO.docx'},
        ],
    },
    {
        'doc': 'PNOPR-007',
        'formatos': [
            {'seq': 10, 'codigo': 'F-PR-007/001', 'nombre': 'Control de temperatura',
             'file': 'F-PR-007-006 Formato control de temp.docx',
             'dl':   'F-PR-007-001 Control de temperatura.docx'},
            {'seq': 20, 'codigo': 'F-PR-007/002', 'nombre': 'Control de temperatura y humedad',
             'file': 'F-PR-007-007 Formato control de temp y humedad.docx',
             'dl':   'F-PR-007-002 Control de temperatura y humedad.docx'},
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
print('Listo: formatos PRODUCCIÓN cargados')
