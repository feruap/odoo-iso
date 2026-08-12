{
    'name': 'Amunet - Registros de formatos',
    'version': '19.0.1.0.0',
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
    'installable': True,
    'application': False,
}
