{
    'name': 'Gestión de Calibración de Equipos (Amunet)',
    'version': '19.0.2.0.0',
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
    'depends': ['base', 'mail', 'amunet_quality'],
    'data': [
        'security/amunet_equipment_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/amunet_equipment_views.xml',
        'views/amunet_equipment_calibration_views.xml',
        'views/amunet_calibration_program_views.xml',
        'views/amunet_quality_test_line_inherit_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
