{
    'name': 'Listas de materiales para entregas',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Delivery',
    'summary': 'Generación automática de componentes en entregas usando listas de materiales',
    'description': """
Listas de materiales para entregas
===================================

Este módulo permite:
* Configurar listas de materiales (BOMs) para productos
* Generar automáticamente líneas de componentes en entregas
* Calcular cantidades según factor multiplicador
* Integración con sistema de lotes Amunet

Características principales:
* Una BOM por producto
* Generación automática con onchange
* Visibilidad condicional en entregas
* Compatible con lotes Amunet
    """,
    'author': 'DIC Consultores',
    'website': 'https://www.amunet.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'product',
        'amunet_lot',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/amunet_transfer_bom_views.xml',
        'views/stock_picking_type_views.xml',
        'views/stock_picking_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
