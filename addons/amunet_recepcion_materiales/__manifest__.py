{
    'name': 'Recepción de Materiales MP',
    'version': '19.0.1.0.0',
    'summary': 'Captura de lote del proveedor, fecha de fabricación y caducidad en recepciones',
    'category': 'Inventory',
    'author': 'Amunet',
    'depends': ['amunet_lot', 'stock'],
    'data': [
        'reports/report_recepcion_materiales.xml',
        'views/stock_picking_views.xml',
        'views/stock_lot_alert_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
