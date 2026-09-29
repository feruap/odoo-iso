{
    'name': 'Amunet - Tablero de producción (plan vs real)',
    'version': '19.0.1.0.1',
    'summary': 'Piezas planeadas vs piezas terminadas por día, sin importes',
    'author': 'Amunet',
    'license': 'LGPL-3',
    'category': 'Manufacturing',
    'depends': ['mrp', 'spreadsheet_dashboard'],
    'data': [
        'security/ir.model.access.csv',
        'views/produccion_diaria_views.xml',
        'data/dashboards.xml',
    ],
    'post_init_hook': '_post_init_plan',
    'installable': True,
    'application': False,
}
