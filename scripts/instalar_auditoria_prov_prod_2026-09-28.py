# Instala en produccion los dos modulos del hub de Auditorias a proveedores que
# pidio Documentacion (validado por ellos en staging el 25-sep) y aprobo Mery.
#
# El CI solo corre `-u` de los modulos que cambiaron; un modulo nuevo NO se
# instala solo. Se hace aqui con la ORM, no por SQL.
#
# Probado antes sobre un clon del dump de hoy (db_20260928_085115): exit 0,
# quedan instalados los dos mas sus tres dependencias, con sus menus.
M = env['ir.module.module'].sudo()
QUIERO = ('amunet_apertura_cierre_prov', 'amunet_proveedores')

print('=== antes ===')
for n in QUIERO:
    print('  %-34s %s' % (n, M.search([('name','=',n)], limit=1).state))

mods = M.search([('name','in',QUIERO)])
assert len(mods) == 2, 'no aparecen los dos modulos en la lista'
mods.button_immediate_install()
env.cr.commit()

print()
print('=== despues ===')
for n in ('amunet_apertura_cierre_prov','amunet_proveedores','amunet_checklist_auditoria_prov',
          'amunet_plan_auditoria_proveedores','amunet_programa_auditoria_proveedores'):
    m = M.search([('name','=',n)], limit=1)
    print('  %-40s %-12s v%s' % (n, m.state, m.latest_version or '-'))

print()
print('=== menus de las dos tarjetas ===')
for x in env['ir.ui.menu'].sudo().search([]):
    xid = x.get_external_id().get(x.id, '')
    if xid.startswith(('amunet_apertura_cierre_prov.', 'amunet_proveedores.')):
        print('  %-46s padre: %s' % (x.name, x.parent_id.name or '(raiz)'))
