# -*- coding: utf-8 -*-

{
    'name': 'Amunet - Preflight Piloto',
    'summary': 'Checklist preventivo antes de fabricar un piloto',
    'description': """
        Valida antes de iniciar un piloto de fabricacion: BOM, stock,
        calidad, muestreo, empaque, usuarios, capacitacion, equipos y
        cambios abiertos. Es una capa preventiva de ISO 13485; no sustituye
        firmas ni liberaciones formales.
    """,
    'author': 'Amunet',
    'category': 'Manufacturing',
    'version': '19.0.1.1.1',
    'depends': [
        'mail',
        'mrp',
        'stock',
        'amunet_production',
        'amunet_quality',
        'amunet_packaging_planning',
        'amunet_material_request',
        'amunet_competencias',
        'amunet_equipment_calibration',
        'amunet_change_control',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/pilot_preflight_views.xml',
        'views/mrp_production_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
