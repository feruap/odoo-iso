import base64, os

FormModel = env['amunet.documento.formato']
DocModel  = env['amunet.documento']

UPLOADS = '/tmp/formatos_ad'

def b64(filename):
    path = os.path.join(UPLOADS, filename)
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

formatos = [
    {
        'doc_codigo': 'PNOAD-001',
        'registros': [
            {
                'sequence': 10,
                'codigo': 'F-AD-001/001',
                'nombre': 'Revisión por la dirección',
                'filename': 'REVISION POR LA DIRECCION 2023.docx',
            },
            {
                'sequence': 20,
                'codigo': 'F-AD-001/002',
                'nombre': 'Registro de asistencia',
                'filename': 'F-AD-001-002 Registro de asistencia.doc',
            },
        ],
    },
    {
        'doc_codigo': 'PNOAD-002',
        'registros': [
            {
                'sequence': 10,
                'codigo': 'F-AD-002/001',
                'nombre': 'Solicitud de compra',
                'filename': 'Solicitud de compra.docx',
            },
        ],
    },
]

for grupo in formatos:
    doc = DocModel.search([('codigo', '=', grupo['doc_codigo'])], limit=1)
    if not doc:
        print(f'  SKIP — no encontré {grupo["doc_codigo"]}')
        continue

    # Elimina formatos anteriores del mismo documento para no duplicar
    FormModel.search([('documento_id', '=', doc.id)]).unlink()

    for r in grupo['registros']:
        data = b64(r['filename'])
        FormModel.create({
            'documento_id': doc.id,
            'sequence':     r['sequence'],
            'codigo':       r['codigo'],
            'nombre':       r['nombre'],
            'archivo':      data,
            'archivo_filename': r['filename'],
        })
        print(f'  OK — {doc.codigo} → {r["codigo"]} ({r["filename"]})')

env.cr.commit()
print('Listo: formatos PNOAD-001 y PNOAD-002 cargados')
