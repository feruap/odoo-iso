# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Documentos Controlados (ISO 13485 4.2)',
    'summary': 'Gestor de documentos controlados: versiones, vigencias, distribucion y firmas',
    'description': """Control de documentos y registros bajo ISO 13485 (4.2.4/4.2.5):
documento controlado con codigo, version, estado (borrador/en revision/vigente/obsoleto),
responsable, vigencia, archivo, historial de versiones, lista de distribucion con acuse,
y firmas de revision y aprobacion.""",
    'author': 'Amunet',
    'category': 'Quality',
    'version': '19.0.1.0.0',
    'depends': ['mail'],
    'data': [
        'security/amunet_documentos_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/amunet_documento_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
