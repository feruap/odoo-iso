{
    'name': 'Amunet - Control de Vigencias',
    'version': '19.0.1.2.0',
    'category': 'Quality',
    'summary': 'Alertas de vencimiento para registros sanitarios, certificados y permisos (ISO 13485)',
    'author': 'Amunet',
    'license': 'LGPL-3',
    'depends': ['mail', 'amunet_documentos'],
    'data': [
        'security/ir.model.access.csv',
        'security/rules.xml',
        'data/cron.xml',
        'data/seeds_registros_sanitarios.xml',
        'wizard/vencimiento_firma_wizard_views.xml',
        'views/vencimiento_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'amunet_vencimientos/static/src/css/vencimientos.css',
            'amunet_vencimientos/static/src/js/vencimientos_hub.js',
            'amunet_vencimientos/static/src/xml/vencimientos_hub.xml',
        ],
    },
    'installable': True,
    'application': False,
}
