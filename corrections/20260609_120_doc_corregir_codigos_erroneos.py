ERRORES = {
    'F-PR-001/002': 'F-CC-002/001',   # "Registro de ingreso de muestras a CC" — código de área equivocado
    'F-CC-001/002': 'F-CC-002/001',   # ídem
    'F-RH-007/005': 'F-GE-007/002',   # "Revisión de indumentaria" — área equivocada (RH→GE)
    'F-RH-005/011': 'F-RH-004/003',   # "Código de ética" — número de PNO equivocado
    'F-RH-004/005': 'F-RH-005/002',   # "Organigrama" — número de PNO equivocado
    'F-MA-001/002': 'F-MA-001/001',   # "Solicitud de mantenimiento" — no existe /002
}

ActModel = env['amunet.documento.actividad']
total = 0

for act in ActModel.search([]):
    if not act.descripcion:
        continue
    nueva = act.descripcion
    for viejo, nuevo in ERRORES.items():
        if viejo in nueva:
            nueva = nueva.replace(viejo, nuevo)
            total += 1
    if nueva != act.descripcion:
        act.write({'descripcion': nueva})

env.cr.commit()
print(f'OK — {total} errores corregidos')
