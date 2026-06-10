import re

# Mismo mapa de recodificación que se aplicó a descripcion (script 119)
# más correcciones de área errónea (script 120) y typos adicionales de registro
MAPA = {
    # ALMACÉN
    'F-AL-003/002': 'F-AL-003/001',
    'F-AL-007/003': 'F-AL-007/001',
    'F-AL-008/004': 'F-AL-008/001',
    'F-AL-008/005': 'F-AL-008/002',
    # CONTROL DE CALIDAD
    'F-CC-006/003': 'F-CC-006/001',
    'F-CC-009/004': 'F-CC-009/001',
    # DOCUMENTACIÓN
    'F-DC-002/005': 'F-DC-002/001',
    'F-DC-003/006': 'F-DC-003/001',
    'F-DC-003/007': 'F-DC-003/002',
    'F-DC-003/008': 'F-DC-003/003',
    'F-DC-004/009': 'F-DC-004/001',
    'F-DC-004/010': 'F-DC-004/002',
    'F-DC-004/011': 'F-DC-004/003',
    'F-DC-004/012': 'F-DC-004/004',
    'F-DC-004/013': 'F-DC-004/005',
    'F-DC-004/014': 'F-DC-004/006',
    'F-DC-005/015': 'F-DC-005/001',
    'F-DC-005/016': 'F-DC-005/002',
    'F-DC-005/017': 'F-DC-005/003',
    'F-DC-005/018': 'F-DC-005/004',
    'F-DC-005/019': 'F-DC-005/005',
    'F-DC-006/020': 'F-DC-006/001',
    'F-DC-006/021': 'F-DC-006/002',
    'F-DC-006/030': 'F-DC-006/003',
    # ESTABILIDAD
    'F-EST-002/002': 'F-EST-002/001',
    'F-EST-002/003': 'F-EST-002/001',
    'F-EST-003/002': 'F-EST-003/001',
    'F-EST-003/003': 'F-EST-003/001',
    'F-EST-005/004': 'F-EST-005/001',
    # GENERALES
    'F-GE-004/003': 'F-GE-004/001',
    'F-GE-004/004': 'F-GE-004/002',
    'F-GE-007/005': 'F-GE-007/001',
    'F-GE-007/006': 'F-GE-007/002',
    'F-GE-009/005': 'F-GE-009/001',
    'F-GE-009/006': 'F-GE-009/002',
    'F-GE-009/007': 'F-GE-009/003',
    # MANTENIMIENTO
    'F-MA-001/0001': 'F-MA-001/001',  # typo 4 dígitos
    'F-MA-001/002':  'F-MA-001/001',
    'F-MA-003/002':  'F-MA-003/001',
    'F-MA-004/003':  'F-MA-004/001',
    'F-MA-004/004':  'F-MA-004/001',
    # PRODUCCIÓN
    'F-PR-003/002': 'F-PR-003/001',
    'F-PR-003/003': 'F-PR-003/002',
    'F-PR-005/004': 'F-PR-005/001',
    'F-PR-006/005': 'F-PR-006/001',
    'F-PR-006/006': 'F-PR-006/002',
    'F-PR-007/006': 'F-PR-007/001',
    'F-PR-007/007': 'F-PR-007/002',
    # RECURSOS HUMANOS
    'F-RH-002/002': 'F-RH-002/001',
    'F-RH-002/003': 'F-RH-002/002',
    'F-RH-002/005': 'F-RH-002/001',
    'F-RH-002/006': 'F-RH-002/002',
    'F-RH-003/004': 'F-RH-003/001',
    'F-RH-003/005': 'F-RH-003/002',
    'F-RH-003/006': 'F-RH-003/003',
    'F-RH-003/007': 'F-RH-003/004',
    'F-RH-004/005': 'F-RH-005/002',   # número PNO equivocado
    'F-RH-004/008': 'F-RH-004/001',
    'F-RH-004/009': 'F-RH-004/002',
    'F-RH-004/010': 'F-RH-004/003',
    'F-RH-004/011': 'F-RH-004/004',
    'F-RH-005/011': 'F-RH-004/003',   # número PNO equivocado
    'F-RH-005/012': 'F-RH-005/001',
    'F-RH-005/013': 'F-RH-005/002',
    'F-RH-007/005': 'F-GE-007/002',   # área equivocada RH→GE
    'F-RH-007/006': 'F-GE-007/002',   # área equivocada RH→GE
    # TECNOVIGILANCIA
    'F-TV-003/002': 'F-TV-003/001',
    'F-TV-003/003': 'F-TV-003/002',
    'F-TV-004/004': 'F-TV-004/001',
    # ERRORES DE ÁREA
    'F-PR-001/002': 'F-CC-002/001',   # área equivocada PR→CC
    'F-CC-001/002': 'F-CC-002/001',   # número PNO equivocado
    'F-PR-006/003': 'F-CC-006/001',   # área equivocada PR→CC (limpieza CC)
    'F-ES-003/003': 'F-EST-003/001',  # abreviatura ES→EST + contador global
}

ActModel = env['amunet.documento.actividad']
total = 0

for act in ActModel.search([('registro', '!=', False)]):
    nuevo = act.registro
    for viejo, nuevo_cod in MAPA.items():
        if viejo in nuevo:
            nuevo = nuevo.replace(viejo, nuevo_cod)
            total += 1
    if nuevo != act.registro:
        act.write({'registro': nuevo})

env.cr.commit()
print(f'OK — {total} reemplazos realizados en campo registro')
