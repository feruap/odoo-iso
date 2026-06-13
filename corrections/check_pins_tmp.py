User = env['res.users']
Pin = env['amunet.quality.signature.pin']

usuarios = User.search([('share', '=', False), ('active', '=', True)])
pins = Pin.search([])
usuarios_con_pin = pins.mapped('user_id')

print('Total usuarios internos activos: %d' % len(usuarios))
print('Con PIN: %d' % len(usuarios_con_pin))
print('Sin PIN: %d' % len(usuarios - usuarios_con_pin))
print('\nDetalle:')
for u in usuarios.sorted('name'):
    tiene = 'SI' if u in usuarios_con_pin else 'NO'
    print('  %s | %s | %s' % (tiene, u.name, u.login))
