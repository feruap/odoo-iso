{
    'name': 'Recepción de Materiales MP',
    'version': '19.0.2.0.0',
    'summary': 'Inspección de entrada, criterios de aceptación, destino automático y firma con PIN',
    'category': 'Inventory',
    'author': 'Amunet',
    'depends': ['amunet_lot', 'stock', 'amunet_quality', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/recepcion_pin_wizard_views.xml',
        'reports/report_recepcion_materiales.xml',
        'views/product_template_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_lot_alert_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
