# Crea el 2do acceso de Patricia Leany Segundo Ibanez con login
# s.validacion@amunet.com.mx para sus responsabilidades de VALIDACION (no calidad).
# Misma persona, mismos grupos que su cuenta RS (uid 68) EXCEPTO los referentes a
# Calidad / rol regulatorio. Se crea partner propio; NO se re-liga el empleado (ese
# queda en la cuenta RS r.sanitario@). Sin PIN de firma (eso es solo de Calidad).
# Autorizado por Fernando 2026-07-22.
src = env['res.users'].browse(68)
assert src.login == 'r.sanitario@amunet.com.mx', 'uid 68 no es la cuenta RS renombrada'

EXCLUIR = [
    'Calidad / Responsable Sanitario',
    'Documentos: Responsable Sanitario',
    'Documentos: Comité técnico',
]
keep = src.group_ids.filtered(lambda g: g.name not in EXCLUIR)
print('Grupos origen:', len(src.group_ids), '| se conservan:', len(keep), '| se excluyen:', len(src.group_ids) - len(keep))

existe = env['res.users'].with_context(active_test=False).search([('login', '=', 's.validacion@amunet.com.mx')], limit=1)
assert not existe, 'ya existe un usuario con ese login'

new = env['res.users'].create({
    'name': 'Patricia Leany Segundo Ibanez (Validación)',
    'login': 's.validacion@amunet.com.mx',
    'email': 's.validacion@amunet.com.mx',
    'group_ids': [(6, 0, keep.ids)],
})
env.cr.commit()
print('Usuario creado uid:', new.id, '| login:', new.login)
print('Grupos asignados:')
for g in new.group_ids.sorted(lambda x: x.name):
    print('   -', g.name)
print('LISTO')
