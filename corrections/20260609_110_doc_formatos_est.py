import base64, os

F   = env['amunet.documento.formato']
Doc = env['amunet.documento']
DIR = '/tmp/formatos_est'

def b64(filename):
    with open(os.path.join(DIR, filename), 'rb') as f:
        return base64.b64encode(f.read()).decode()

grupos = [
    {
        'doc': 'PNOEST-001',
        'formatos': [
            {
                'seq': 10,
                'codigo': 'F-EST-001/001',
                'nombre': 'Programa anual de estabilidad a largo plazo',
                'file':   'F-EST-001-001 Programa Anual De estabilidad A Largo Plazo VER 02.docx',
                'dl':     'F-EST-001-001 Programa anual de estabilidad a largo plazo.docx',
            },
            {
                'seq': 20,
                'codigo': 'F-EST-001/002',
                'nombre': 'Lista maestra de protocolos y reportes de estabilidad',
                'file':   'F-EST-001-002 Lista maestra de protocolos y reportes de estabilidad.docx',
                'dl':     'F-EST-001-002 Lista maestra de protocolos y reportes de estabilidad.docx',
            },
        ],
    },
    {
        'doc': 'PNOEST-002',
        'formatos': [
            {
                'seq': 10,
                'codigo': 'F-EST-002/001',
                'nombre': 'Programa anual de estabilidad acelerada',
                'file':   'F-EST-002-003 Programa Anual De estabilidad Acelerada VER 02.docx',
                'dl':     'F-EST-002-001 Programa anual de estabilidad acelerada.docx',
            },
        ],
    },
    {
        'doc': 'PNOEST-005',
        'formatos': [
            {
                'seq': 10,
                'codigo': 'F-EST-005/001',
                'nombre': 'Control de temperatura y humedad — estabilidad',
                'file':   'F-EST-005-004 Temperatura y humedad estabilidad.docx',
                'dl':     'F-EST-005-001 Control de temperatura y humedad estabilidad.docx',
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
print('Listo: formatos EST cargados')
