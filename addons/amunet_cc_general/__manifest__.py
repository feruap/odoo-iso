# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Control de Cambios General',
    'summary': 'Control de cambios para formatos, manuales e infraestructura',
    'description': 'Registro de control de cambios general: formatos, manuales, instalaciones y equipos. ISO 13485 / NOM-241.',
    'author': 'Amunet',
    'category': 'Quality',
    'version': '19.0.1.0.0',
    'depends': ['mail', 'amunet_documentos'],
    'data': [
        'security/amunet_cc_general_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'wizard/amunet_cc_rechazo_wizard_views.xml',
        'views/amunet_cc_general_views.xml',
        'views/amunet_documento_ext_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'amunet_cc_general/static/src/css/cc_general.css',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
