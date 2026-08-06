# -*- coding: utf-8 -*-
{
    'name': 'Recepción de combos (2 pasos)',
    'summary': 'Recibir un combo de proveedor (1 SKU) y convertirlo a sus '
               'hojas/insumos individuales, cada uno con su lote Amunet, '
               'heredando el lote de proveedor y fechas capturados 1 sola vez.',
    'version': '19.0.1.7.0',
    'author': 'Amunet',
    'category': 'Inventory/Purchase',
    'depends': ['stock', 'purchase', 'amunet_lot',
                'amunet_recepcion_materiales'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
