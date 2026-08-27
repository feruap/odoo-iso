{
    'name':        'Plan de Auditoría de Proveedores (F-DC-005-016)',
    'version':     '19.0.1.0.0',
    'summary':     'Plan detallado de ejecución de auditoría a proveedor específico',
    'category':    'Quality/Amunet',
    'author':      'Amunet',
    'depends':     ['amunet_documentos', 'amunet_cc_general', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'reports/report_plan_auditoria_proveedor.xml',
        'views/plan_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'license':     'LGPL-3',
}
