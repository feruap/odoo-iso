# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Compras generales (pago y autorizacion)',
    'summary': 'Urgencia de la solicitud, forma de pago, autorizacion por Telegram y seguimiento de pago, embarque y llegada en la orden de compra.',
    'author': 'Amunet',
    'category': 'Inventory/Purchase',
    'version': '19.0.6.0.0',
    # amunet_material_request sigue siendo dependencia por res.users.amunet_material_head_id
    # (el jefe directo) y por el grupo group_material_manager (area de compras).
    # purchase_stock: la orden de compra ahora lleva seguimiento de pago y llegada.
    'depends': ['amunet_material_request', 'amunet_marketplace', 'purchase_stock'],
    'data': [
        'security/security.xml',
        'security/usuarios_pagos.xml',
        'security/ir.model.access.csv',
        'views/solicitud_compra_views.xml',
        'views/material_request_views.xml',
        'views/purchase_order_views.xml',
        'views/seguimiento_views.xml',
    ],
    'post_init_hook': 'post_init_generar_secreto',
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
