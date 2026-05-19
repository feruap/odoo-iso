"""Assign work queue roles for support areas.

The script is intentionally login-based and only touches named support users.
"""

assignments = {
    'rrhh@amunet.com.mx': [
        'amunet_competencias.group_competencias_manager',
        'amunet_competencias.group_competencias_user',
    ],
    'mantenimiento@amunet.com.mx': [
        'amunet_equipment_calibration.group_maintenance_technician',
    ],
}

Users = env['res.users'].sudo().with_context(active_test=False)

for login, xmlids in assignments.items():
    user = Users.search([('login', '=', login)], limit=1)
    if not user:
        print('WORKQUEUE_ROLE_SKIP missing %s' % login)
        continue
    commands = []
    for xmlid in xmlids:
        group = env.ref(xmlid, raise_if_not_found=False)
        if group:
            commands.append((4, group.id))
        else:
            print('WORKQUEUE_ROLE_SKIP missing group %s for %s' % (xmlid, login))
    if commands:
        user.write({'group_ids': commands})
        print('WORKQUEUE_ROLE_ASSIGNED %s' % login)

env.cr.commit()
