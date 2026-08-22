User = env['res.users']
stacey = User.search([('login', '=', 'documentacion@amunet.com.mx')], limit=1)
print('Usuario: %s (id=%d)' % (stacey.name, stacey.id))
print('Grupos:')
for g in stacey.groups_id.sorted('name'):
    if 'document' in g.full_name.lower() or 'document' in (g.category_id.name or '').lower():
        print('  [DOC] %s' % g.full_name)
print('Es manager de documentos: %s' % stacey.has_group('amunet_documentos.group_documentos_manager'))
print('Es user de documentos:    %s' % stacey.has_group('amunet_documentos.group_documentos_user'))
