# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Visibilidad de precios restringida',
    'summary': 'Oculta precios de costo y venta a todos excepto al grupo "Ver precios" (Fernando).',
    'description': """
Restringe la visibilidad de precios sensibles a los usuarios que pertenecen al
grupo "Ver precios". Los demas usuarios (incluyendo compras y almacen) pueden
seguir operando normalmente (crear ordenes de compra, recibir mercancia, etc.)
pero NO veran:

* Precio de venta (list_price) en producto
* Costo (standard_price) en producto
* Precio unitario en informacion de proveedor (supplierinfo.price)
* Precio unitario, subtotal y total en lineas y orden de compra
* Importes en facturas de proveedor para el modulo de compras

Solo el usuario asignado al grupo "Amunet / Ver precios" tiene acceso completo.
    """,
    'author': 'Amunet',
    'category': 'Hidden',
    'version': '19.0.1.0.0',
    'depends': [
        'product',
        'purchase',
        'stock',
    ],
    'data': [
        'security/security.xml',
        'data/price_viewer_user.xml',
        'views/product_views.xml',
        'views/supplierinfo_views.xml',
        'views/purchase_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
