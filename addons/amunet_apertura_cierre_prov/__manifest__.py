{
    'name':        'Registro de Apertura y Cierre de Auditoría de Proveedores (F-DC-005-017)',
    'version':     '19.0.1.0.0',
    'summary':     'Registro de reuniones de apertura y cierre en auditoría a proveedor',
    'category':    'Quality/Amunet',
    'author':      'Amunet',
    'depends':     ['amunet_documentos', 'amunet_plan_auditoria_proveedores', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'reports/report_apertura_cierre.xml',
        'views/registro_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'license':     'LGPL-3',
}
