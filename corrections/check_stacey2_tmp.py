User = env['res.users']
stacey = User.search([('login', '=', 'documentacion@amunet.com.mx')], limit=1)
print('Usuario: %s (id=%d)' % (stacey.name, stacey.id))
print('Es manager de documentos: %s' % stacey.has_group('amunet_documentos.group_documentos_manager'))
print('Es user de documentos:    %s' % stacey.has_group('amunet_documentos.group_documentos_user'))

# Ver menú items disponibles para ella
menus = env['ir.ui.menu'].with_user(stacey.id).search([
    ('parent_id.name', 'in', ['Control de Documentos', 'Documentacion', 'Documentación'])
])
print('\nMenus visibles para Stacey bajo Control de Documentos:')
for m in menus.sorted('sequence'):
    print('  seq=%s %s' % (m.sequence, m.name))
