# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Documentos Controlados (ISO 13485 4.2 / NOM-241-SSA1-2025)',
    'summary': 'Gestor de documentos controlados: versiones, vigencias, distribucion, firmas y reportes',
    'description': """Control de documentos y registros bajo ISO 13485 (4.2.4/4.2.5) y NOM-241-SSA1-2025 (5.2):
documento controlado con codigo, version, estado, responsable, area, vigencia, archivo,
historial de versiones, firmas, secciones segun PNOGE-001, sugerencias de cambio y politicas
de firmas configurables.""",
    'author': 'Amunet',
    'category': 'Quality',
    'version': '19.0.5.0.0',
    'depends': ['mail', 'amunet_quality'],
    'data': [
        'security/amunet_documentos_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/amunet_firma_config_views.xml',
        'views/amunet_sugerencia_views.xml',
        'views/amunet_documento_views.xml',
        'views/report_lista_maestra.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
