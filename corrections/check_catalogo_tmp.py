Cat = env['amunet.catalogo.firma']
registros = Cat.search([])
print('Registros en catálogo: %d' % len(registros))
con_pin = registros.filtered(lambda r: r.tiene_pin)
sin_pin = registros.filtered(lambda r: not r.tiene_pin)
print('Con PIN: %d' % len(con_pin))
print('Sin PIN: %d' % len(sin_pin))
for r in sin_pin:
    print('  SIN PIN: %s' % r.user_name)
