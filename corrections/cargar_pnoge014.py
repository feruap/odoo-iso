# -*- coding: utf-8 -*-
# Carga el PNOGE-014 "Asignacion de Numeros de Lote" a la biblioteca de
# documentos (amunet.documento). Archivo docx preparado por Documentacion
# (Nextcloud). Autorizado por Fernando 2026-07-13.
#  Elaboro: Stacy (69) | Reviso: Mery (61) | Autorizo: Patricia Leany (68, RS)
import base64

Doc = env['amunet.documento']
if Doc.search([('codigo', '=', 'PNOGE-014')], limit=1):
    print("PNOGE-014 YA EXISTE, no se crea.")
else:
    with open('/tmp/pnoge014.docx', 'rb') as f:
        datos = base64.b64encode(f.read())
    vals = {
        'codigo': 'PNOGE-014',
        'name': 'ASIGNACIÓN DE NÚMEROS DE LOTE',
        'tipo': 'pno',
        'state': 'vigente',
        'area': 'GE',
        'version_actual': '01',
        'elabora_id': 69,       # Stacy Palma
        'revisor_id': 61,       # Mery Olivares
        'autorizador_id': 68,   # Patricia Leany (Responsable Sanitario)
        'responsable_id': 69,   # Stacy (Documentacion)
        'archivo': datos,
        'archivo_filename': 'PNOGE-014 Asignacion de Numeros de Lote.docx',
        'fecha_vigencia': '2026-07-13',
    }
    d = Doc.create(vals)
    print("CREADO PNOGE-014 id=%s state=%s" % (d.id, d.state))
env.cr.commit()
print("LISTO")
