# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Layout de menús de Producción',
    'summary': 'Consolida los menús de producción: oculta la app '
               '"Producción Amunet" y reacomoda Empaque, Preflight, No '
               'conformidad, Supervisiones y Almacén de reactivos bajo la '
               '"Producción" base de Odoo. Solo reorganiza menús; no toca lógica.',
    'version': '19.0.1.0.0',
    'author': 'Amunet',
    'category': 'Manufacturing',
    'depends': [
        'mrp',
        'amunet_production',
        'amunet_packaging_planning',
        'amunet_pilot_preflight',
        'amunet_rework_control',
        'amunet_process_inspection',
    ],
    'data': ['data/menu_layout.xml'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
