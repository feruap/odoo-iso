# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Desviaciones y Control de Cambios',
    'summary': 'Desviaciones por lote, cambios documentales e impresion controlada',
    'description': """
        Flujo ISO 13485 para desviaciones, sustituciones controladas,
        cambios temporales por lote, cambios documentales permanentes y
        solicitudes de impresion de manuales/instructivos.
    """,
    'author': 'Amunet',
    'category': 'Quality',
    'version': '19.0.1.0.0',
    'depends': [
        'mail',
        'stock',
        'mrp',
        'amunet_quality',
        'amunet_production',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/amunet_change_control_views.xml',
        'views/amunet_quality_check_views.xml',
        'views/mrp_production_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
