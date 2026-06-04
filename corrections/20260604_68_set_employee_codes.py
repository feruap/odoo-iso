# Asigna código de empleado 019 a Diana en staging
emp = env['hr.employee'].search([('user_id.login', '=', 's.controldecalidad@amunet.com.mx')], limit=1)
if not emp:
    print("ERROR: no se encontró el empleado de Diana")
else:
    emp.write({'employee_code': '019'})
    # Sincronizar también en res.users directamente
    emp.user_id.sudo().write({'employee_code': '019'})
    env.cr.commit()
    print(f"OK: código 019 asignado a {emp.name}")
    print(f"  res.users.employee_code = {emp.user_id.employee_code}")
