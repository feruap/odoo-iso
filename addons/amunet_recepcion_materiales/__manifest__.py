{
    'name': 'Recepción de Materiales MP',
    'version': '19.0.1.0.0',
    'summary': 'Captura de lote del proveedor, fecha de fabricación y caducidad en recepciones',
    'category': 'Inventory',
    'author': 'Amunet',
    'depends': ['amunet_lot', 'stock'],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
}
