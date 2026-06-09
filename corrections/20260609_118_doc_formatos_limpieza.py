import base64, os

F   = env['amunet.documento.formato']
Doc = env['amunet.documento']
DIR = '/tmp/formatos_limpieza'

def b64(filename):
    with open(os.path.join(DIR, filename), 'rb') as f:
        return base64.b64encode(f.read()).decode()

# PNOCC-006: reemplaza F-CC-006/001
doc = Doc.search([('codigo', '=', 'PNOCC-006')], limit=1)
rec = F.search([('documento_id', '=', doc.id), ('codigo', '=', 'F-CC-006/001')], limit=1)
rec.write({
    'nombre':           'Bitácora de limpieza de control de calidad',
    'archivo':          b64('F-CC-006-003 Bitacora Limpieza control.docx'),
    'archivo_filename': 'F-CC-006-001 Bitacora de limpieza de control de calidad.docx',
})
print(f'  OK — PNOCC-006 → F-CC-006/001 actualizado')

# PNOPR-003: reemplaza F-PR-003/002
doc = Doc.search([('codigo', '=', 'PNOPR-003')], limit=1)
rec = F.search([('documento_id', '=', doc.id), ('codigo', '=', 'F-PR-003/002')], limit=1)
rec.write({
    'nombre':           'Bitácora de limpieza de producción',
    'archivo':          b64('F-PR-003-003 Bitacora Limpieza Producción.docx'),
    'archivo_filename': 'F-PR-003-002 Bitacora de limpieza de produccion.docx',
})
print(f'  OK — PNOPR-003 → F-PR-003/002 actualizado')

# PNOEST-003: nuevo
doc = Doc.search([('codigo', '=', 'PNOEST-003')], limit=1)
F.search([('documento_id', '=', doc.id)]).unlink()
F.create({
    'documento_id':     doc.id,
    'sequence':         10,
    'codigo':           'F-EST-003/001',
    'nombre':           'Bitácora de limpieza de estabilidad',
    'archivo':          b64('F-EST-003-003 Bitacora Limpieza Estabilidad.docx'),
    'archivo_filename': 'F-EST-003-001 Bitacora de limpieza de estabilidad.docx',
})
print(f'  OK — PNOEST-003 → F-EST-003/001 nuevo')

# PNOAL-003: nuevo
doc = Doc.search([('codigo', '=', 'PNOAL-003')], limit=1)
F.search([('documento_id', '=', doc.id)]).unlink()
F.create({
    'documento_id':     doc.id,
    'sequence':         10,
    'codigo':           'F-AL-003/001',
    'nombre':           'Bitácora de limpieza de almacén MP',
    'archivo':          b64('F-AL-003-002 Bitacora Limpieza de Almacén MP.docx'),
    'archivo_filename': 'F-AL-003-001 Bitacora de limpieza de almacen MP.docx',
})
print(f'  OK — PNOAL-003 → F-AL-003/001 nuevo')

env.cr.commit()
print('Listo: formatos de limpieza cargados')
