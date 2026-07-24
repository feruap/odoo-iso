# -*- coding: utf-8 -*-

{
    'name': 'Amunet - Conector WooCommerce',
    'summary': 'Sincronizacion de inventario Odoo hacia WooCommerce por API REST',
    'description': """Conecta el inventario de Odoo con la tienda WooCommerce
(www.amunet.com.mx / tst.amunet.com.mx). Empareja productos por SKU y publica
las existencias de producto terminado en WooCommerce mediante la API REST
(wc/v3), con bitacora auditable de cada sincronizacion.""",
    'author': 'Amunet',
    'category': 'Inventory',
    'version': '19.0.1.0.0',
    'depends': [
        'mail',
        'stock',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/woo_backend_views.xml',
        'views/woo_product_mapping_views.xml',
        'views/woo_sync_log_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
