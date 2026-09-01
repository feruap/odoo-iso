{
    'name': 'Amunet - Gestión de Riesgos (AMEF)',
    'version': '19.0.1.0.0',
    'category': 'Quality',
    'summary': 'AMEF: Severidad × Ocurrencia × Detectabilidad (1-5) para ISO 13485',
    'author': 'Amunet',
    'license': 'LGPL-3',
    'depends': ['mail', 'amunet_registros', 'amunet_desviaciones'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/risk_criteria_data.xml',
        'views/risk_matrix_views.xml',
        'views/risk_analysis_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
}
