# Crea el empleado de la cuenta de validacion de Patricia (uid 113) como
# SUPERVISOR del area de Desarrollo. Con esto:
#  - Monitor Temp: el area "Desarrollo" (id 13) deriva su supervisor de un empleado
#    en el depto Desarrollo con puesto "Supervisor" -> sera uid 113.
#  - Solicitudes de Material: el "Jefe de area" = department.manager_id -> uid 113.
# Depto Desarrollo = id 3, puesto Supervisor = hr.job id 2. Es un 2do empleado de la
# misma persona (el 1ro sigue ligado a su cuenta RS uid 68). Autorizado Fernando 2026-07-22.
Emp = env['hr.employee'].sudo()
Dept = env['hr.department'].sudo()

assert not Emp.search([('user_id', '=', 113)]), 'uid 113 ya tiene empleado'
u = env['res.users'].browse(113)
assert u.exists() and u.login == 's.validacion@amunet.com.mx'

emp = Emp.create({
    'name': 'Patricia Leany Segundo Ibanez (Validación)',
    'user_id': 113,
    'department_id': 3,   # Desarrollo
    'job_id': 2,          # Supervisor
    'work_email': 's.validacion@amunet.com.mx',
})
print('Empleado creado id:', emp.id, '| depto:', emp.department_id.name, '| puesto:', emp.job_id.name)

Dept.browse(3).write({'manager_id': emp.id})
print('Manager del depto Desarrollo:', Dept.browse(3).manager_id.name)

env.cr.commit()

# Verificar derivacion del supervisor en el area de temp Desarrollo (id 13)
area = env['amunet.temp.area'].sudo().browse(13)
print('Supervisor derivado del area temp Desarrollo:', area.supervisor_user_id.name or '(ninguno)')
print('LISTO')
