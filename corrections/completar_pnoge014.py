# Completa el registro de control de PNOGE-014 para dejarlo consistente con el
# resto de la biblioteca: crea el registro de version v01 (vigente) y setea la
# fecha de publicacion/emision. El documento ya estaba vigente y autorizado por
# Patricia (uid 68); solo faltaban estos datos de control.
from datetime import date

doc = env['amunet.documento'].search([('codigo', '=', 'PNOGE-014')], limit=1)
assert doc, 'PNOGE-014 no encontrado'
d = date(2026, 7, 13)

vals = {}
if not doc.fecha_publicacion:
    vals['fecha_publicacion'] = d
if not doc.fecha_emision:
    vals['fecha_emision'] = d
if vals:
    doc.write(vals)

Ver = env['amunet.documento.version']
if not Ver.search([('documento_id', '=', doc.id), ('version', '=', '01')]):
    Ver.create({
        'documento_id': doc.id,
        'version': '01',
        'fecha': d,
        'fecha_emision': d,
        'state_historico': 'vigente',
        'descripcion_cambio': 'Elaboracion del documento - Creacion del documento, Revision, Correccion, Modificacion, Mejora continua',
    })

env.cr.commit()

doc = env['amunet.documento'].search([('codigo', '=', 'PNOGE-014')], limit=1)
n = Ver.search_count([('documento_id', '=', doc.id)])
print('fecha_publicacion:', doc.fecha_publicacion)
print('fecha_emision   :', doc.fecha_emision)
print('n_versiones     :', n)
print('state           :', doc.state)
