{
    'name': 'Amunet - Acta de Apertura y Cierre de Auditoría',
    'version': '19.0.1.0.0',
    'category': 'Quality',
    'summary': 'Registro de reuniones de apertura y cierre (ISO 13485 §8.2.4)',
    'author': 'Amunet',
    'license': 'LGPL-3',
    'depends': ['amunet_documentos', 'amunet_quality', 'amunet_plan_auditorias'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'reports/report_acta_auditoria.xml',
        'views/acta_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
}
