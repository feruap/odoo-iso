# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Compras generales (pago y autorizacion)',
    'summary': 'Forma de pago, monto y datos de transferencia en la solicitud de compra general.',
    'author': 'Amunet',
    'category': 'Inventory/Purchase',
    'version': '19.0.3.0.0',
    'depends': ['amunet_material_request', 'amunet_marketplace'],
    'data': ['security/security.xml', 'views/material_request_views.xml'],
    'post_init_hook': 'post_init_generar_secreto',
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
