{
    'name': 'Amunet - Lista de Verificación de Auditoría',
    'version': '19.0.1.0.0',
    'category': 'Quality',
    'summary': 'Lista de verificación por secciones durante la ejecución de la auditoría interna',
    'author': 'Amunet',
    'license': 'LGPL-3',
    'depends': ['amunet_documentos', 'amunet_quality', 'amunet_plan_auditorias'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/lista_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
}
