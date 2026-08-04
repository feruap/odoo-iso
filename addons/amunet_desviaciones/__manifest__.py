{
    'name': 'Amunet - Desviaciones y No Conformidades',
    'version': '19.0.1.0.0',
    'category': 'Quality',
    'summary': 'Registro y seguimiento de desviaciones y no conformidades (ISO 13485)',
    'author': 'Amunet',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'amunet_documentos', 'amunet_quality', 'amunet_cc_general'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/amunet_desviacion_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
