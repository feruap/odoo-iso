# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Compras generales (pago y autorizacion)',
    'summary': 'Forma de pago, monto, datos de transferencia y autorizacion por Telegram en la solicitud de compra del Marketplace interno.',
    'author': 'Amunet',
    'category': 'Inventory/Purchase',
    'version': '19.0.5.0.0',
    # amunet_material_request sigue siendo dependencia por res.users.amunet_material_head_id
    # (el jefe directo) y por el grupo group_material_manager (area de compras).
    'depends': ['amunet_material_request', 'amunet_marketplace'],
    'data': ['security/security.xml', 'views/solicitud_compra_views.xml'],
    'post_init_hook': 'post_init_generar_secreto',
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
