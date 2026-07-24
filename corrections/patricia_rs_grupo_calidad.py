# Agrega a Patricia Leany Segundo Ibanez (uid 68) al grupo Responsable Sanitario
# de Calidad. Autorizado por Fernando 2026-07-20.
u = env['res.users'].browse(68)
g = env.ref('amunet_quality.group_quality_sanitary')
assert u.exists() and u.login == 's.validacion@amunet.com.mx', 'usuario 68 inesperado'
antes = g in u.group_ids
u.write({'group_ids': [(4, g.id)]})
print('Usuario:', u.name, '| ya estaba en RS:', antes, '| ahora en RS:', g in u.all_group_ids)
env.cr.commit()
