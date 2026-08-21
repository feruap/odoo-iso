{
    'name':    'Checklist de Auditoría Técnica a Proveedores',
    'version': '19.0.1.0.0',
    'summary': 'Formato único adaptable: Crítico, Importante y General (F-DC-005-018)',
    'category': 'Quality/Amunet',
    'author':  'Amunet',
    'depends': ['amunet_documentos', 'amunet_plan_auditoria_proveedores', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'reports/report_checklist.xml',
        'views/checklist_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
