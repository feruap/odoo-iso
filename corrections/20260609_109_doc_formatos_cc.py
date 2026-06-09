import base64, os

F   = env['amunet.documento.formato']
Doc = env['amunet.documento']
DIR = '/tmp/formatos_cc'

def b64(filename):
    with open(os.path.join(DIR, filename), 'rb') as f:
        return base64.b64encode(f.read()).decode()

grupos = [
    {
        'doc': 'PNOCC-001',
        'formatos': [
            {
                'seq': 10,
                'codigo': 'F-CC-001/001',
                'nombre': 'Producto no conforme',
                'file':   'F-CC-001-001 producto no conforme.docx',
                'dl':     'F-CC-001-001 Producto no conforme.docx',
            },
        ],
    },
    {
        'doc': 'PNOCC-002',
        'formatos': [
            {
                'seq': 10,
                'codigo': 'F-CC-002/001',
                'nombre': 'Ingreso de muestras a control de calidad',
                'file':   'F-CC-002-002 ingreso de muestras a cc ver 02.docx',
                'dl':     'F-CC-002-001 Ingreso de muestras a control de calidad.docx',
            },
        ],
    },
    {
        'doc': 'PNOCC-006',
        'formatos': [
            {
                'seq': 10,
                'codigo': 'F-CC-006/001',
                'nombre': 'Limpieza del área de control de calidad',
                'file':   'F-CC-006-003 LIMPIEZA DE CALIDAD.docx',
                'dl':     'F-CC-006-001 Limpieza del area de control de calidad.docx',
            },
        ],
    },
    {
        'doc': 'PNOCC-009',
        'formatos': [
            {
                'seq': 10,
                'codigo': 'F-CC-009/001',
                'nombre': 'Control de temperatura y humedad',
                'file':   'F-CC-009-004 Formato control de temp y humedad.docx',
                'dl':     'F-CC-009-001 Control de temperatura y humedad.docx',
            },
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
print('Listo: formatos CC cargados')
