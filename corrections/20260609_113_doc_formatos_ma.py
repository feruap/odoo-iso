import base64, os

F   = env['amunet.documento.formato']
Doc = env['amunet.documento']
DIR = '/tmp/formatos_ma'

def b64(filename):
    with open(os.path.join(DIR, filename), 'rb') as f:
        return base64.b64encode(f.read()).decode()

grupos = [
    {
        'doc': 'PNOMA-001',
        'formatos': [
            {'seq': 10, 'codigo': 'F-MA-001/001', 'nombre': 'Mantenimiento a la infraestructura',
             'file': 'F-MA-001-001 Mantenimiento a la infraestructura.docx',
             'dl':   'F-MA-001-001 Mantenimiento a la infraestructura.docx'},
        ],
    },
    {
        'doc': 'PNOMA-004',
        'formatos': [
            {'seq': 10, 'codigo': 'F-MA-004/001', 'nombre': 'Programa anual de prevención de fauna nociva',
             'file': 'F-MA-004-004 Programa anual prevención de fauna nociva.docx',
             'dl':   'F-MA-004-001 Programa anual de prevencion de fauna nociva.docx'},
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
print('Listo: formatos MANTENIMIENTO cargados')
