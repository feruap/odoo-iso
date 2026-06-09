import base64, os

F   = env['amunet.documento.formato']
Doc = env['amunet.documento']
DIR = '/tmp/formatos_rh'

def b64(filename):
    with open(os.path.join(DIR, filename), 'rb') as f:
        return base64.b64encode(f.read()).decode()

grupos = [
    {
        'doc': 'PNORH-001',
        'formatos': [
            {'seq': 10, 'codigo': 'F-RH-001/001', 'nombre': 'Catálogo de firmas',
             'file': 'F-RH-001-001 CATALOGO DE FIRMAS.docx',
             'dl':   'F-RH-001-001 Catalogo de firmas.docx'},
        ],
    },
    {
        'doc': 'PNORH-002',
        'formatos': [
            {'seq': 10, 'codigo': 'F-RH-002/001', 'nombre': 'Programa anual de capacitación, evaluación y calificación',
             'file': 'F-RH-002-002 Programa Anual capacitación, eval. y calif.2024..docx',
             'dl':   'F-RH-002-001 Programa anual de capacitacion evaluacion y calificacion.docx'},
            {'seq': 20, 'codigo': 'F-RH-002/002', 'nombre': 'Calificación de personal',
             'file': 'F-RH-002-003 Calificacion de Personal.doc',
             'dl':   'F-RH-002-002 Calificacion de personal.doc'},
        ],
    },
    {
        'doc': 'PNORH-003',
        'formatos': [
            {'seq': 10, 'codigo': 'F-RH-003/001', 'nombre': 'Programa de capacitación',
             'file': 'F-RH-003-004 PROGRAMA DE CAPACITACION.docx',
             'dl':   'F-RH-003-001 Programa de capacitacion.docx'},
            {'seq': 20, 'codigo': 'F-RH-003/002', 'nombre': 'Registro de asistencia de capacitación',
             'file': 'F-RH-003-005 REGISTRO DE ASISTENCIA DE CAPAC.doc',
             'dl':   'F-RH-003-002 Registro de asistencia de capacitacion.doc'},
            {'seq': 30, 'codigo': 'F-RH-003/003', 'nombre': 'Evaluación de conocimientos',
             'file': 'F-RH-003-006 EVAL DE CONOCIMIENTOS FORMATO.doc',
             'dl':   'F-RH-003-003 Evaluacion de conocimientos.doc'},
            {'seq': 40, 'codigo': 'F-RH-003/004', 'nombre': 'Solicitud de capacitación externa',
             'file': 'F-RH-003-007 SOLICITUD DE CAPACITACION EXTERNA.docx',
             'dl':   'F-RH-003-004 Solicitud de capacitacion externa.docx'},
        ],
    },
    {
        'doc': 'PNORH-004',
        'formatos': [
            {'seq': 10, 'codigo': 'F-RH-004/001', 'nombre': 'Requisición de personal',
             'file': 'F-RH-004-008 Requisición de personal.docx',
             'dl':   'F-RH-004-001 Requisicion de personal.docx'},
            {'seq': 20, 'codigo': 'F-RH-004/002', 'nombre': 'Lista de documentos',
             'file': 'F-RH-004-009 LISTA DE DOCUMENTOS.docx',
             'dl':   'F-RH-004-002 Lista de documentos.docx'},
            {'seq': 30, 'codigo': 'F-RH-004/003', 'nombre': 'Código de ética',
             'file': 'F-RH-004-010 CODIGO DE ETICA AMUNET.docx',
             'dl':   'F-RH-004-003 Codigo de etica.docx'},
            {'seq': 40, 'codigo': 'F-RH-004/004', 'nombre': 'Carta compromiso de confidencialidad',
             'file': 'F-RH-004-011 CARTA COMPROMIS DE CONFIDENCIALIDAD AMUNET.docx',
             'dl':   'F-RH-004-004 Carta compromiso de confidencialidad.docx'},
        ],
    },
    {
        'doc': 'PNORH-005',
        'formatos': [
            {'seq': 10, 'codigo': 'F-RH-005/001', 'nombre': 'Organigrama funcional',
             'file': 'F-RH-005-012 Organigrama Funcional_V02.docx',
             'dl':   'F-RH-005-001 Organigrama funcional.docx'},
            {'seq': 20, 'codigo': 'F-RH-005/002', 'nombre': 'Organigrama',
             'file': 'F-RH-005-013 Organigrama.docx',
             'dl':   'F-RH-005-002 Organigrama.docx'},
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
print('Listo: formatos RRHH cargados')
