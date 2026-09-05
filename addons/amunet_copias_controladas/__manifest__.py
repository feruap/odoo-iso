{
    'name': 'Amunet - Copias Controladas de Certificados',
    'version': '19.0.1.0.0',
    'category': 'Quality',
    'summary': 'Registro y acuse de copias controladas de certificados de calidad (ISO 13485 §4.2.4)',
    'author': 'Amunet',
    'license': 'LGPL-3',
    'depends': ['amunet_documentos', 'amunet_quality'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/copia_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
}
