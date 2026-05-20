# -*- coding: utf-8 -*-

{
    'name': 'Amunet - Planeacion de Empaque',
    'summary': 'Presentaciones autorizadas, tendencia WooCommerce y reacondicionamiento',
    'description': """
        Planea la mezcla de empaque de una orden de fabricacion usando
        tendencia historica de WooCommerce. Controla presentaciones
        autorizadas y reacondicionamientos entre cajas autorizadas.
    """,
    'author': 'Amunet',
    'category': 'Manufacturing',
    'version': '19.0.1.0.0',
    'depends': [
        'mail',
        'mrp',
        'stock',
        'amunet_production',
        'amunet_label',
        'amunet_quality',
        'amunet_change_control',
        'amunet_material_request',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/packaging_presentation_views.xml',
        'views/woo_sales_trend_views.xml',
        'views/packaging_plan_views.xml',
        'views/packaging_rework_views.xml',
        'views/mrp_production_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
