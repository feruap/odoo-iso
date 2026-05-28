{
    'name': 'Gestión de Calibración de Equipos (Amunet)',
    'version': '19.0.3.3.0',
    'category': 'Quality',
    'summary': 'Control de equipos, calibraciones y trazabilidad ISO 13485',
    'description': """
Módulo de Gestión de Calibración de Equipos (ISO 13485 Cláusula 7.6).
- Inventario de Equipos Críticos.
- Registro y control de calibraciones (Certificados, vigencia).
- Bloqueo automático de equipos vencidos.
- Trazabilidad en controles de calidad (amunet_quality).
    """,
    'author': 'Amunet',
    'website': 'https://www.amunet.com',
    'depends': ['base', 'mail', 'amunet_quality', 'amunet_lot'],
    'data': [
        'security/amunet_equipment_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/amunet_equipment_views.xml',
        'views/amunet_equipment_calibration_views.xml',
        'views/amunet_calibration_program_views.xml',
        'views/amunet_maintenance_program_views.xml',
        'views/amunet_quality_test_line_inherit_views.xml',
        'views/amunet_equipment_serial_views.xml',
        'views/product_template_views.xml',
        'views/stock_lot_views.xml',
        'views/amunet_expediente_views.xml',
        'views/menus.xml',
        'views/amunet_workqueue_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
