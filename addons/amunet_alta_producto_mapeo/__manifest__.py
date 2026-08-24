# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Alta de producto desde el mapeo (propuesta)',
    'version': '19.0.1.0.0',
    'summary': 'Boton en el mapeo Woo para PROPONER el alta de un producto nuevo '
               '(flujo propuesta -> aprobacion). Anti-duplicados (incl. archivados), '
               'clave propuesta y tipo de suministro. Aprueban Mery o Fernando.',
    'author': 'Amunet - Agente PM',
    'depends': ['amunet_marketplace', 'amunet_woocommerce', 'amunet_woo_revision'],
    'data': [
        'views/alta_producto_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
