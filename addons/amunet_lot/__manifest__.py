# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Lotes',
    'version': '19.0.1.0.1',
    'summary': 'Generación automática de secuencias de lotes',
    'description': """
        Módulo de gestión de lotes simplificado que utiliza stock.lot nativo de Odoo con denominación secuencial automática por producto.
        
        Diferencia clave con amunet_lot_sequence: 
            - Utiliza stock.lot directamente (sin modelo intermedio).
            - Generación automática de secuencias en la creación de lotes.
            - Prefijos configurables por producto.
            - Restablecimiento de secuencia mensual opcional.
    """,
    'author': 'Rafael López Flores',
    'category': 'Inventory/Inventory',
    'depends': [
        'stock',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/stock_picking_type_data.xml',
        'views/product_template_views.xml',
        # PRUEBA: Desactivando vistas una por una para encontrar el problema
        # Empezando por las más simples
        'views/amunet_lot_factory_views.xml',
        'views/stock_lot_views.xml',
        'views/stock_quant_views.xml',
        'views/stock_scrap_views.xml',
        'views/stock_picking_views.xml',
        # Vistas de stock_move_line
        'views/stock_move_line_views.xml',
        'views/stock_move_line_actions.xml',
        'views/stock_move_operations_views.xml',
        'views/stock_picking_type_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'amunet_lot/static/src/xml/stock_traceability_report.xml',
            'amunet_lot/static/src/xml/lots_dialog.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

