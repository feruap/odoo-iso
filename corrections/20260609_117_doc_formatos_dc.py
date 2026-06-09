import base64, os

F   = env['amunet.documento.formato']
Doc = env['amunet.documento']
DIR = '/tmp/formatos_dc'

def b64(filename):
    with open(os.path.join(DIR, filename), 'rb') as f:
        return base64.b64encode(f.read()).decode()

grupos = [
    {
        'doc': 'PNODC-001',
        'formatos': [
            {'seq': 10, 'codigo': 'F-DC-001/001', 'nombre': 'Registro de documentos',
             'file': 'F-DC-001-001 REG DE DOCUMENTOS.docx',
             'dl':   'F-DC-001-001 Registro de documentos.docx'},
            {'seq': 20, 'codigo': 'F-DC-001/002', 'nombre': 'Copias controladas',
             'file': 'F-DC-001-002 Copias controladas.docx',
             'dl':   'F-DC-001-002 Copias controladas.docx'},
            {'seq': 30, 'codigo': 'F-DC-001/003', 'nombre': 'Registro de documentos de consulta',
             'file': 'F-DC-001-003 REG DE DOCUMENTOS DE CONSULTA.docx',
             'dl':   'F-DC-001-003 Registro de documentos de consulta.docx'},
            {'seq': 40, 'codigo': 'F-DC-001/004', 'nombre': 'Registro de destrucción de documentos obsoletos',
             'file': 'F-DC-001-004 REG DE DESTRUCCION DE DOCUMENTOS OBSOLETOS.docx',
             'dl':   'F-DC-001-004 Registro de destruccion de documentos obsoletos.docx'},
        ],
    },
    {
        'doc': 'PNODC-002',
        'formatos': [
            {'seq': 10, 'codigo': 'F-DC-002/001', 'nombre': 'Cierre de lote de fabricación',
             'file': 'F-DC-002-005 cierre lote de fabricación.docx',
             'dl':   'F-DC-002-001 Cierre de lote de fabricacion.docx'},
        ],
    },
    {
        'doc': 'PNODC-003',
        'formatos': [
            {'seq': 10, 'codigo': 'F-DC-003/001', 'nombre': 'Convocatoria',
             'file': 'F-DC-003-006 CONVOCATORIA.docx',
             'dl':   'F-DC-003-001 Convocatoria.docx'},
            {'seq': 20, 'codigo': 'F-DC-003/002', 'nombre': 'Entrevista a auditor',
             'file': 'F-DC-003-007 ENTREVISTA AUDITOR.docx',
             'dl':   'F-DC-003-002 Entrevista a auditor.docx'},
            {'seq': 30, 'codigo': 'F-DC-003/003', 'nombre': 'Resultados',
             'file': 'F-DC-003-008 RESULTADOS.docx',
             'dl':   'F-DC-003-003 Resultados.docx'},
        ],
    },
    {
        'doc': 'PNODC-004',
        'formatos': [
            {'seq': 10, 'codigo': 'F-DC-004/001', 'nombre': 'Programa de auditorías internas',
             'file': 'F-DC-004-009 PROGRAMA DE AUDITORIAS INTERNAS.docx',
             'dl':   'F-DC-004-001 Programa de auditorias internas.docx'},
            {'seq': 20, 'codigo': 'F-DC-004/002', 'nombre': 'Plan de auditoría',
             'file': 'F-DC-004-010 Plan de auditoria.docx',
             'dl':   'F-DC-004-002 Plan de auditoria.docx'},
            {'seq': 30, 'codigo': 'F-DC-004/003', 'nombre': 'Registro anual de auditorías internas',
             'file': 'F-DC-004-011 REGISTRO ANUAL DE AUDITORIAS INTERNAS.docx',
             'dl':   'F-DC-004-003 Registro anual de auditorias internas.docx'},
            {'seq': 40, 'codigo': 'F-DC-004/004', 'nombre': 'Apertura y cierre de auditoría interna',
             'file': 'F-DC-004-012 APERTURA Y CIERRE DE AUDITORIA INTERNA.docx',
             'dl':   'F-DC-004-004 Apertura y cierre de auditoria interna.docx'},
            {'seq': 50, 'codigo': 'F-DC-004/005', 'nombre': 'Lista de verificación',
             'file': 'F-DC-004-013 Lista de verificación.docx',
             'dl':   'F-DC-004-005 Lista de verificacion.docx'},
            {'seq': 60, 'codigo': 'F-DC-004/006', 'nombre': 'Informe de auditoría interna',
             'file': 'F-DC-004-014 INFORME DE AUDITORIA INTERNA.docx',
             'dl':   'F-DC-004-006 Informe de auditoria interna.docx'},
        ],
    },
    {
        'doc': 'PNODC-005',
        'formatos': [
            {'seq': 10, 'codigo': 'F-DC-005/001', 'nombre': 'Programa de auditoría técnica a proveedores',
             'file': 'F-DC-005-015 PROGRAMA DE AUDITORIA TECNICAS PROVEEDORES.docx',
             'dl':   'F-DC-005-001 Programa de auditoria tecnica a proveedores.docx'},
            {'seq': 20, 'codigo': 'F-DC-005/002', 'nombre': 'Plan de auditoría de proveedores',
             'file': 'F-DC-005-016 PLAN DE AUDITORIA DE PROVEEDORES.docx',
             'dl':   'F-DC-005-002 Plan de auditoria de proveedores.docx'},
            {'seq': 30, 'codigo': 'F-DC-005/003', 'nombre': 'Apertura y cierre de auditoría de proveedores',
             'file': 'F-DC-005-017 APERTURA Y CIERRE DE AUDITORIA DE PROVEEDORES.docx',
             'dl':   'F-DC-005-003 Apertura y cierre de auditoria de proveedores.docx'},
            {'seq': 40, 'codigo': 'F-DC-005/004', 'nombre': 'Reporte de auditoría de proveedores',
             'file': 'F-DC-005-018 REPORTE DE AUDITORIA PROVEEDORES.docx',
             'dl':   'F-DC-005-004 Reporte de auditoria de proveedores.docx'},
            {'seq': 50, 'codigo': 'F-DC-005/005', 'nombre': 'Informe de auditoría de proveedores',
             'file': 'F-DC-005-019 INFORME DE AUDITORIA DE PROVEEDORES.docx',
             'dl':   'F-DC-005-005 Informe de auditoria de proveedores.docx'},
        ],
    },
    {
        'doc': 'PNODC-006',
        'formatos': [
            {'seq': 10, 'codigo': 'F-DC-006/001', 'nombre': 'Lista de proveedores críticos',
             'file': 'F-DC-006-020 LISTA DE PROVEEDORES CRITICOS.docx',
             'dl':   'F-DC-006-001 Lista de proveedores criticos.docx'},
            {'seq': 20, 'codigo': 'F-DC-006/002', 'nombre': 'Reporte de calificación de proveedores',
             'file': 'F-DC-006-021 REPORE DE CALIFICACIÓN PROVEEDORES.docx',
             'dl':   'F-DC-006-002 Reporte de calificacion de proveedores.docx'},
            {'seq': 30, 'codigo': 'F-DC-006/003', 'nombre': 'Lista de proveedores',
             'file': 'F-DC-006-030 LISTA DE PROVEEDORES.docx',
             'dl':   'F-DC-006-003 Lista de proveedores.docx'},
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
print('Listo: formatos DOCUMENTACIÓN cargados')
