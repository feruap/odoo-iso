{
    'name': 'Amunet - Programa Anual de Auditorías',
    'version': '19.0.1.0.0',
    'category': 'Quality',
    'summary': 'Programa anual de auditorías internas (ISO 13485 §8.2.4)',
    'author': 'Amunet',
    'license': 'LGPL-3',
    'depends': ['amunet_documentos', 'amunet_quality'],
    'data': [
        'security/ir.model.access.csv',
        'views/reprogramar_wizard_views.xml',
        'views/programa_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
}
