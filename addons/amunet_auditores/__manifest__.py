{
    'name': 'Amunet - Selección y Formación de Auditores Internos',
    'version': '19.0.1.0.0',
    'category': 'Quality',
    'summary': 'Convocatorias, evaluación y registro de auditores internos (PNODC-003)',
    'author': 'Amunet',
    'license': 'LGPL-3',
    'depends': ['mail', 'amunet_documentos'],
    'data': [
        'security/ir.model.access.csv',
        'data/criterios_data.xml',
        'data/preguntas_data.xml',
        'views/convocatoria_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
}
