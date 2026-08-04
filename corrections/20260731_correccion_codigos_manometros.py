# -*- coding: utf-8 -*-
# Corrección de códigos de manómetros/compresor (solicitud Ensayo, validado en
# staging con Jorge). Replica el estado objetivo de staging a producción.
# Datos regulatorios de metrología; NO toca precios. Idempotente.
Eq = env['amunet.equipment']
Line = env['amunet.calibration.program.line']

def show(label):
    for e in Eq.browse([93, 94, 95, 201, 202]).exists():
        print("  ", label, e.id, e.serial_number, e.state, e.department,
              "padre=%s" % (e.parent_equipment_id.id or '-'))

print("=== ANTES ==="); show("EQ")

# 1. Compresor de aire (93): PRO/BOM/01 -> PRO/COM/01
comp = Eq.browse(93)
if comp.exists() and comp.serial_number == 'PRO/BOM/01':
    comp.write({'serial_number': 'PRO/COM/01'})
    print("  [1] compresor 93 -> PRO/COM/01")

# 2-3. Manómetros duplicados (94, 95): out_of_service
dups = Eq.browse([94, 95]).exists().filtered(lambda e: e.state != 'out_of_service')
if dups:
    dups.write({'state': 'out_of_service'})
    print("  [2-3] 94/95 -> out_of_service")

# 4-5. Manómetros COM (201, 202): depto INYECCIÓN + padre = compresor 93
for mid in (201, 202):
    m = Eq.browse(mid)
    if m.exists() and (m.department != 'INYECCIÓN' or m.parent_equipment_id.id != 93):
        m.write({'department': 'INYECCIÓN', 'parent_equipment_id': 93})
        print("  [4-5] %s -> INYECCIÓN, padre=93" % mid)

# 6. Programa de calibración
#    a) borrar líneas de los códigos viejos PRO/BOM/01-1 y PRO/BOM/01-2 (eq 94,95)
viejas = Line.search([('equipment_id', 'in', [94, 95])])
if viejas:
    print("  [6a] borrando líneas de programa:", viejas.mapped('identification_code'))
    viejas.unlink()
#    b) actualizar líneas PRO/COM/01-1 y PRO/COM/01-2 (eq 201,202)
comlines = Line.search([('equipment_id', 'in', [201, 202])])
for ln in comlines:
    if ln.area_prefix != 'PRO' or ln.department_final != 'INYECCIÓN':
        ln.write({'area_prefix': 'PRO', 'department_final': 'INYECCIÓN'})
        print("  [6b] línea eq %s -> area_prefix=PRO, dept=INYECCIÓN" % ln.equipment_id.id)

print("=== DESPUÉS ==="); show("EQ")
print("Líneas programa (201/202):", [(l.equipment_id.id, l.area_prefix, l.department_final) for l in Line.search([('equipment_id','in',[201,202])])])
print("Líneas programa (94/95):", Line.search_count([('equipment_id','in',[94,95])]), "(debe ser 0)")
env.cr.commit()
