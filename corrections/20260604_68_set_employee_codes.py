"""
Asigna códigos de empleado (3 dígitos) para firmas QC.
RE-EJECUTABLE: correr cada vez que staging se refresque desde producción.

Códigos:
  019 - Diana Flores Vera       (s.controldecalidad@amunet.com.mx)
  020 - Gabriela Solares Páez   (analista1cc@amunet.com.mx)
  005 - Rodrigo Torres Cortés   (analista2cc@amunet.com.mx)
"""

CODIGOS = [
    ('s.controldecalidad@amunet.com.mx', '019', 'Diana Flores Vera'),
    ('analista1cc@amunet.com.mx',        '020', 'Gabriela Solares Páez'),
    ('analista2cc@amunet.com.mx',        '005', 'Rodrigo Torres Cortés'),
]

for login, codigo, nombre in CODIGOS:
    emp = env['hr.employee'].search([('user_id.login', '=', login)], limit=1)
    if not emp:
        print(f"  NO ENCONTRADO: {login}")
        continue
    emp.write({'employee_code': codigo})
    emp.user_id.sudo().write({'employee_code': codigo})
    print(f"  OK: {nombre} → {codigo}")

env.cr.commit()
print("Listo.")
