{
    'name': 'Amunet - Ciclo de Vida ISO 13485',
    'summary': 'Quejas, diseño y gestión de riesgos trazables',
    'description': '''Cubre retroalimentación y quejas, controles de diseño y
desarrollo, transferencia, y gestión de riesgos enlazada a CAPA, documentos y
controles de cambio.''',
    'version': '19.0.1.0.0',
    'category': 'Quality',
    'author': 'Amunet',
    'license': 'LGPL-3',
    'depends': [
        'mail', 'product', 'stock', 'amunet_quality', 'amunet_documentos',
        'amunet_change_control',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/complaint_views.xml',
        'views/design_views.xml',
        'views/risk_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
}
