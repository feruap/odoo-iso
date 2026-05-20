# -*- coding: utf-8 -*-
"""Assign pilot permissions required for the short-route manufacturing pilot."""

assignments = [
    ('analista2cc@amunet.com.mx', 'amunet_quality.group_quality_user'),
]

Users = env['res.users'].sudo()

for login, group_xmlid in assignments:
    user = Users.search([('login', '=', login)], limit=1)
    if not user:
        print('PILOT_PERMISSION_USER_NOT_FOUND %s' % login)
        continue

    group = env.ref(group_xmlid).sudo()
    if group not in user.group_ids:
        user.write({'group_ids': [(4, group.id)]})
        print('PILOT_PERMISSION_ASSIGNED %s %s' % (login, group_xmlid))
    else:
        print('PILOT_PERMISSION_ALREADY_SET %s %s' % (login, group_xmlid))

env.cr.commit()
print('PILOT_PERMISSIONS_COMMIT_OK')
