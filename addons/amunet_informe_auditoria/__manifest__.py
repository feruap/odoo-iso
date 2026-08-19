{
    'name': 'Amunet - Informe de Auditoría Interna',
    'version': '19.0.1.0.0',
    'category': 'Quality',
    'summary': 'Informe de resultados de la auditoría interna (ISO 13485 §8.2.4)',
    'author': 'Amunet',
    'license': 'LGPL-3',
    'depends': ['amunet_documentos', 'amunet_quality', 'amunet_plan_auditorias'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/informe_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
}
