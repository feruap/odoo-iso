"""Assign Amunet production operator/supervisor roles.

This correction is intentionally login-based: it only changes the named
production users and avoids broad group rewrites.
"""

operator_logins = {
    'operador1@amunet.com.mx',
    'operador2@amunet.com.mx',
    'operador3@amunet.com.mx',
}

supervisor_logins = {
    's.produccion@amunet.com.mx',
    'produccionsub@amunet.com.mx',
}

operator_group = env.ref('amunet_production.group_production_operator')
supervisor_group = env.ref('amunet_production.group_production_supervisor')
mrp_user_group = env.ref('mrp.group_mrp_user')
stock_user_group = env.ref('stock.group_stock_user')
stock_lot_group = env.ref('stock.group_tracking_lot')
material_requester_group = env.ref('amunet_material_request.group_material_requester')

Users = env['res.users'].sudo().with_context(active_test=False)

for login in sorted(operator_logins):
    user = Users.search([('login', '=', login)], limit=1)
    if not user:
        print('PROD_ROLE_SKIP missing operator %s' % login)
        continue
    user.write({
        'group_ids': [
            (4, operator_group.id),
            (4, material_requester_group.id),
            (3, mrp_user_group.id),
            (3, stock_user_group.id),
            (3, stock_lot_group.id),
        ],
    })
    print('PROD_ROLE_OPERATOR %s' % login)

for login in sorted(supervisor_logins):
    user = Users.search([('login', '=', login)], limit=1)
    if not user:
        print('PROD_ROLE_SKIP missing supervisor %s' % login)
        continue
    user.write({
        'group_ids': [
            (4, supervisor_group.id),
            (4, operator_group.id),
            (4, material_requester_group.id),
            (4, mrp_user_group.id),
            (4, stock_user_group.id),
            (4, stock_lot_group.id),
        ],
    })
    print('PROD_ROLE_SUPERVISOR %s' % login)

env.cr.commit()
