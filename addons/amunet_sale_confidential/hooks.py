# -*- coding: utf-8 -*-
"""Al instalar, otorga el grupo confidencial a quien ya administra Ventas.

Sin esto, restringir el menu de Ventas dejaria sin acceso incluso a los
administradores que hoy son los unicos con grupo de ventas.
"""


def post_init_hook(env):
    confidential = env.ref(
        'amunet_sale_confidential.group_sale_confidential', raise_if_not_found=False)
    manager = env.ref('sales_team.group_sale_manager', raise_if_not_found=False)
    if not confidential or not manager:
        return
    users = env['res.users'].search([('all_group_ids', 'in', manager.id)])
    if users:
        confidential.sudo().write({'user_ids': [(4, u.id) for u in users]})
