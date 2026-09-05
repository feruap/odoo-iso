{
    'name': 'Amunet - Expediente de Auditoría',
    'version': '19.0.1.0.0',
    'category': 'Quality',
    'summary': 'Vista resumen con plan, acta, lista de verificación e informe de cada auditoría',
    'author': 'Amunet',
    'license': 'LGPL-3',
    'depends': [
        'amunet_plan_auditorias',
        'amunet_acta_auditoria',
        'amunet_lista_verificacion',
        'amunet_informe_auditoria',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/expediente_views.xml',
    ],
    'installable': True,
    'application': False,
}
