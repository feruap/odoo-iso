# -*- coding: utf-8 -*-

{
    'name': 'Amunet - No Conformidad y Reproceso',
    'summary': 'Control ISO 13485 de producto no conforme, reproceso y re-QC',
    'description': """
        Registra no conformidades detectadas por Calidad, bloquea el lote
        operacionalmente, controla disposicion/reproceso, material adicional,
        ejecucion de Produccion, reanalisis y cierre.
    """,
    'author': 'Amunet',
    'category': 'Quality',
    'version': '19.0.1.0.0',
    'depends': [
        'mail',
        'mrp',
        'stock',
        'amunet_quality',
        'amunet_production',
        'amunet_material_request',
        'amunet_change_control',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/rework_order_views.xml',
        'views/amunet_quality_check_views.xml',
        'views/mrp_production_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
