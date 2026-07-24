# -*- coding: utf-8 -*-
# Renovacion de los 133 registros CAP-AUTO vencidos el 2026-07-09.
# Autorizado por Fernando 2026-07-10. Parte 1 (sin curso ligado).
# Crea 1 registro nuevo por cada CAP-AUTO vencido, mismo empleado + PNO,
# training_date=2026-07-09, expiry_date=2027-07-09, modalidad Presencial.
# Los 133 vencidos se CONSERVAN (historial ISO). Idempotente: no duplica si
# ya existe una renovacion (mismo user+procedure) con vigencia 2027-07-09.

SRC_EXPIRY = '2026-07-09'
NEW_TRAIN = '2026-07-09'
NEW_EXPIRY = '2027-07-09'

Reg = env['amunet.registro.capacitacion']
fuente = Reg.search([('name', 'like', 'CAP-AUTO%'), ('expiry_date', '=', SRC_EXPIRY)])
print("registros fuente (vencidos 2026-07-09):", len(fuente))

# Set de (user, procedure) que YA tienen renovacion vigente 2027-07-09 (corridas previas)
existentes = set()
for x in Reg.search([('expiry_date', '=', NEW_EXPIRY)]):
    existentes.add((x.user_id.id, x.procedure_id.id))
print("renovaciones preexistentes 2027-07-09:", len(existentes))

creados = 0
saltados = 0
for r in fuente:
    clave = (r.user_id.id, r.procedure_id.id)
    if clave in existentes:
        saltados += 1
        continue
    Reg.create({
        'user_id': r.user_id.id,
        'employee_id': r.employee_id.id if r.employee_id else False,
        'department_id': r.department_id.id if r.department_id else False,
        'procedure_id': r.procedure_id.id if r.procedure_id else False,
        'parameter_id': r.parameter_id.id if r.parameter_id else False,
        'trainer_id': r.trainer_id.id if r.trainer_id else False,
        'training_date': NEW_TRAIN,
        'expiry_date': NEW_EXPIRY,
        'training_type': 'presencial',
    })
    creados += 1

env.cr.commit()
print("CREADOS:", creados, "| SALTADOS (ya existian):", saltados)
vig = Reg.search_count([('expiry_date', '=', NEW_EXPIRY), ('training_date', '=', NEW_TRAIN)])
print("TOTAL registros con vigencia 2027-07-09:", vig)
