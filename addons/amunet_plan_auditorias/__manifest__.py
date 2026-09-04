{
    'name': 'Amunet - Plan de Auditoría Interna',
    'version': '19.0.1.0.0',
    'category': 'Quality',
    'summary': 'Plan detallado de auditoría interna (ISO 13485 §8.2.4)',
    'author': 'Amunet',
    'license': 'LGPL-3',
    'depends': ['amunet_documentos', 'amunet_auditores', 'amunet_quality'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir.rules.xml',
        'data/sequences.xml',
        'reports/report_plan_auditoria.xml',
        'views/plan_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
}
