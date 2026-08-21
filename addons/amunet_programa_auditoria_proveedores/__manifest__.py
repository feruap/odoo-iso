{
    'name': 'Amunet - Programa de Auditoría a Técnicas de Proveedores',
    'version': '19.0.1.0.0',
    'category': 'Quality',
    'summary': 'Programa anual de auditoría a técnicas de proveedores (F-DC-005-015)',
    'author': 'Amunet',
    'license': 'LGPL-3',
    'depends': ['amunet_documentos'],
    'data': [
        'security/ir.model.access.csv',
        'views/programa_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}
