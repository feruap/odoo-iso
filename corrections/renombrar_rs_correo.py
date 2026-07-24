# Renombra la cuenta del Responsable Sanitario (uid 68, Patricia Leany Segundo
# Ibanez): login/correo s.validacion@amunet.com.mx -> r.sanitario@amunet.com.mx.
# Conserva nombre, grupos, PIN de firma, capacitacion y las firmas historicas
# (solo cambia el correo). Libera s.validacion@ para un usuario nuevo. Autorizado
# por Fernando 2026-07-22.
NEW = 'r.sanitario@amunet.com.mx'
OLD = 's.validacion@amunet.com.mx'
u = env['res.users'].browse(68)
assert u.exists(), 'uid 68 no existe'
assert u.login == OLD, 'login inesperado: %s' % u.login
print('Antes -> login:', u.login, '| nombre:', u.name)

u.write({'login': NEW})
u.partner_id.write({'email': NEW})

emp = env['hr.employee'].sudo().search([('user_id', '=', 68)])
if emp:
    emp.write({'work_email': NEW})
    print('Empleado actualizado:', emp.name, '-> work_email', NEW)

env.cr.commit()

u2 = env['res.users'].browse(68)
print('Despues -> login:', u2.login, '| email partner:', u2.partner_id.email)
print('PIN sigue:', bool(env['amunet.quality.signature.pin'].search([('user_id','=',68)])))
print('Grupos:', len(u2.groups_id), '| firmas Autorizo historicas conservadas (referencian uid 68)')
print('LISTO')
