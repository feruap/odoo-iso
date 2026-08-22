# Verificación: ¿a quién le aparece "Validar Recepción"?
karla = env['res.users'].browse(78)
veronica = env['res.users'].browse(62)

g_manager  = env.ref('amunet_material_request.group_material_manager')
g_warehouse = env.ref('amunet_material_request.group_material_warehouse')
g_requester = env.ref('amunet_material_request.group_material_requester')

# Grupos directos en BD
env.cr.execute("SELECT gid FROM res_groups_users_rel WHERE uid=62")
v_gids = [r[0] for r in env.cr.fetchall()]
env.cr.execute("SELECT gid FROM res_groups_users_rel WHERE uid=78")
k_gids = [r[0] for r in env.cr.fetchall()]

print("Verónica gids directos: " + str(v_gids))
print("  tiene manager(132): " + str(132 in v_gids))
print("  tiene warehouse(131): " + str(131 in v_gids))
print("  tiene requester(130): " + str(130 in v_gids))

print("Karla gids directos: " + str(k_gids))
print("  tiene manager(132): " + str(132 in k_gids))
print("  tiene warehouse(131): " + str(131 in k_gids))
print("  tiene requester(130): " + str(130 in k_gids))

# Buscar una solicitud en estado pending_reception hecha por Karla
solicitudes = env['amunet.material.request'].search(
    [('state', '=', 'pending_reception'), ('requester_id', '=', karla.id)],
    limit=3
)
print("\nSolicitudes de Karla en estado 'pending_reception': %d" % len(solicitudes))
if solicitudes:
    for sol in solicitudes:
        sol_veronica = sol.with_user(veronica)
        sol_karla    = sol.with_user(karla)
        sol_veronica.invalidate_recordset()
        sol_karla.invalidate_recordset()
        print("  Folio %s:" % sol.name)
        print("    can_validate_reception para Verónica: %s" % sol_veronica.can_validate_reception)
        print("    can_validate_reception para Karla:    %s" % sol_karla.can_validate_reception)
else:
    # Buscar cualquier solicitud de Karla
    any_sol = env['amunet.material.request'].search([('requester_id', '=', karla.id)], limit=3)
    print("Solicitudes de Karla (cualquier estado): %d" % len(any_sol))
    for sol in any_sol:
        print("  Folio %s estado=%s" % (sol.name, sol.state))
