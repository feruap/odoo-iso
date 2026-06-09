import base64, os

F   = env['amunet.documento.formato']
Doc = env['amunet.documento']
DIR = '/tmp/formatos_al'

def b64(filename):
    with open(os.path.join(DIR, filename), 'rb') as f:
        return base64.b64encode(f.read()).decode()

grupos = [
    {
        'doc': 'PNOAL-002',
        'formatos': [
            {
                'seq': 10,
                'codigo': 'F-AL-002/001',
                'nombre': 'Entrada, salida y conciliación de insumos',
                'file':   'F-AL-002-001 Entrada Salida y Conciliación de Insumos ver02.docx',
                'dl':     'F-AL-002-001 Entrada salida y conciliacion de insumos.docx',
            },
        ],
    },
    {
        'doc': 'PNOAL-007',
        'formatos': [
            {
                'seq': 10,
                'codigo': 'F-AL-007/001',
                'nombre': 'Registro de reactivos',
                'file':   'F-AL-007-003_Registro_de_reactivos.docx',
                'dl':     'F-AL-007-001 Registro de reactivos.docx',
            },
            {
                'seq': 20,
                'codigo': 'F-AL-007/002',
                'nombre': 'Registro de reactivos — 1 solo uso',
                'file':   'F-AL-007-003_Registro_de_reactivos 1 solo uso.docx',
                'dl':     'F-AL-007-002 Registro de reactivos 1 solo uso.docx',
            },
        ],
    },
    {
        'doc': 'PNOAL-008',
        'formatos': [
            {
                'seq': 10,
                'codigo': 'F-AL-008/001',
                'nombre': 'Control de temperatura y humedad',
                'file':   'F-AL-008-004 Formato control de temp y humedad.docx',
                'dl':     'F-AL-008-001 Control de temperatura y humedad.docx',
            },
            {
                'seq': 20,
                'codigo': 'F-AL-008/002',
                'nombre': 'Registro de temperatura del refrigerador',
                'file':   'F-AL-008-005 Registro de temperatura del refrigerador.docx',
                'dl':     'F-AL-008-002 Registro de temperatura del refrigerador.docx',
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
print('Listo: formatos ALMACÉN cargados')
