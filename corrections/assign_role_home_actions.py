# -*- coding: utf-8 -*-

PROTECTED_LOGINS = {
    '__system__',
    'admin',
    'admin_disabled_2026-05-08',
    'fernando.ruiz@amunet.com.mx',
    'desarrollo@amunet.com.mx',
}


def _ref(xmlid):
    return env.ref(xmlid, raise_if_not_found=False)


SYSTEM_GROUP = _ref('base.group_system')


def _is_protected(user):
    return (
        not user.active
        or user.login in PROTECTED_LOGINS
        or (SYSTEM_GROUP and SYSTEM_GROUP in user.group_ids)
    )


def _users_in_group(xmlid):
    group = _ref(xmlid)
    if not group:
        print('HOME_ACTION_GROUP_MISSING', xmlid)
        return env['res.users']
    return env['res.users'].with_context(active_test=False).search([
        ('active', '=', True),
        ('group_ids', 'in', group.id),
    ])


def _set_home(user, action_xmlid, reason):
    if _is_protected(user):
        print('HOME_ACTION_SKIPPED_PROTECTED', user.login, reason)
        return

    action = _ref(action_xmlid)
    if not action:
        print('HOME_ACTION_MISSING', action_xmlid, user.login, reason)
        return

    if user.action_id.id == action.id:
        print('HOME_ACTION_ALREADY', user.login, action_xmlid, reason)
        return

    old = user.action_id.name if user.action_id else ''
    user.sudo().write({'action_id': action.id})
    print('HOME_ACTION_SET', user.login, action_xmlid, reason, 'old=', old)


def _has_group(user, xmlid):
    group = _ref(xmlid)
    return bool(group and group in user.group_ids)


def _set_menu_groups(menu_xmlid, group_xmlids, reason):
    menu = _ref(menu_xmlid)
    if not menu:
        print('MENU_VISIBILITY_MISSING', menu_xmlid, reason)
        return

    groups = env['res.groups']
    missing = []
    for group_xmlid in group_xmlids:
        group = _ref(group_xmlid)
        if group:
            groups |= group
        else:
            missing.append(group_xmlid)

    if missing:
        print('MENU_VISIBILITY_GROUP_MISSING', menu_xmlid, missing, reason)

    old = ','.join(menu.group_ids.get_external_id().get(g.id, g.name) for g in menu.group_ids)
    menu.sudo().write({'group_ids': [(6, 0, groups.ids)]})
    print('MENU_VISIBILITY_SET', menu_xmlid, reason, 'old=', old)


_set_menu_groups(
    'contacts.menu_contacts',
    ['base.group_partner_manager', 'base.group_erp_manager', 'base.group_system'],
    'hide_contacts_from_operational_staff',
)
_set_menu_groups(
    'spreadsheet_dashboard.spreadsheet_dashboard_menu_root',
    ['base.group_erp_manager', 'base.group_system'],
    'hide_dashboards_from_operational_staff',
)
_set_menu_groups(
    'base.menu_management',
    ['base.group_system'],
    'hide_apps_from_operational_staff',
)
_set_menu_groups(
    'base.menu_tests',
    ['base.group_no_one'],
    'hide_tests_from_operational_staff',
)


supervisors = _users_in_group('amunet_production.group_production_supervisor')
for user in supervisors:
    _set_home(user, 'mrp.mrp_production_action', 'production_supervisor')

for user in _users_in_group('amunet_production.group_production_operator'):
    if user in supervisors:
        continue
    _set_home(
        user,
        'amunet_production.action_amunet_operator_workorders',
        'production_operator',
    )

for user in _users_in_group('amunet_equipment_calibration.group_maintenance_technician'):
    _set_home(
        user,
        'amunet_equipment_calibration.action_amunet_maintenance_my_work',
        'maintenance_technician',
    )

for user in _users_in_group('amunet_equipment_calibration.group_equipment_manager'):
    _set_home(
        user,
        'amunet_equipment_calibration.action_amunet_metrology_my_work',
        'metrology_manager',
    )

quality_groups = [
    'amunet_quality.group_quality_user',
    'amunet_quality.group_quality_supervisor',
    'amunet_quality.group_quality_sanitary',
    'amunet_quality.group_quality_manager',
]
quality_users = env['res.users']
for group_xmlid in quality_groups:
    quality_users |= _users_in_group(group_xmlid)
for user in quality_users:
    _set_home(
        user,
        'amunet_quality.action_amunet_quality_my_work',
        'quality_workqueue',
    )

for login in ['rrhh@amunet.com.mx']:
    user = env['res.users'].with_context(active_test=False).search(
        [('login', '=', login), ('active', '=', True)], limit=1
    )
    if user and _has_group(user, 'amunet_competencias.group_competencias_manager'):
        _set_home(
            user,
            'amunet_competencias.action_amunet_rrhh_renewals_work',
            'rrhh_competencias',
        )
    else:
        print('HOME_ACTION_RRHH_NOT_FOUND_OR_NO_GROUP', login)

env.cr.commit()
print('HOME_ACTION_COMMIT_OK')
