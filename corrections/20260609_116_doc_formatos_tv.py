import base64, os

F   = env['amunet.documento.formato']
Doc = env['amunet.documento']
DIR = '/tmp/formatos_tv'

def b64(filename):
    with open(os.path.join(DIR, filename), 'rb') as f:
        return base64.b64encode(f.read()).decode()

grupos = [
    {
        'doc': 'PNOTV-001',
        'formatos': [
            {'seq': 10, 'codigo': 'F-TV-001/001', 'nombre': 'Reporte de quejas',
             'file': 'F-TV-001_001 Reporte de Quejas.docx',
             'dl':   'F-TV-001-001 Reporte de quejas.docx'},
            {'seq': 20, 'codigo': 'F-TV-001/002', 'nombre': 'Registro de quejas',
             'file': 'F-TV-001_002 Registro de Quejas.docx',
             'dl':   'F-TV-001-002 Registro de quejas.docx'},
        ],
    },
    {
        'doc': 'PNOTV-003',
        'formatos': [
            {'seq': 10, 'codigo': 'F-TV-003/001', 'nombre': 'Registro de productos retirados del mercado',
             'file': 'F-TV-003_002 Registro de Productos Retirados de Mercado.docx',
             'dl':   'F-TV-003-001 Registro de productos retirados del mercado.docx'},
            {'seq': 20, 'codigo': 'F-TV-003/002', 'nombre': 'Reporte de retiro de producto',
             'file': 'F-TV-003_003 Reporte de Retiro de Producto.docx',
             'dl':   'F-TV-003-002 Reporte de retiro de producto.docx'},
        ],
    },
    {
        'doc': 'PNOTV-004',
        'formatos': [
            {'seq': 10, 'codigo': 'F-TV-004/001', 'nombre': 'Devoluciones',
             'file': 'F-TV-004_004 Devoluciones.docx',
             'dl':   'F-TV-004-001 Devoluciones.docx'},
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
print('Listo: formatos TECNOVIGILANCIA cargados')
