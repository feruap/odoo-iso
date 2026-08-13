{
    'name': 'Amunet - Registros de formatos',
    'version': '19.0.1.0.1',
    'category': 'Quality',
    'summary': 'Captura digital de formatos ISO 13485 (PNOGE, PNODC y otros)',
    'author': 'Amunet',
    'license': 'LGPL-3',
    'depends': ['mail', 'amunet_documentos'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/amunet_reg_vestimenta_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'amunet_registros/static/src/js/registros_hub.js',
            'amunet_registros/static/src/xml/registros_hub.xml',
        ],
    },
    'installable': True,
    'application': False,
}
