# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Competencias y Capacitación (ISO 13485 §6.2)',
    'version': '19.0.1.0.0',
    'category': 'Quality',
    'summary': 'Matriz de habilidades y bloqueo de firma por competencia vencida',
    'description': """
        Gestión de Capacitación para analistas de calidad bajo ISO 13485 Cláusula 6.2.

        Funcionalidades:
        - Registros de capacitación con fecha de caducidad
        - Matriz de competencias por usuario / SOP / Parámetro
        - Bloqueo pre-PIN: impide firmar un control de calidad si la capacitación está vencida
        - Configurable via parámetro de sistema (on/off)
    """,
    'author': 'DIC Consultores - Rafael López Flores',
    'website': 'https://www.amunet.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'amunet_quality',
        'hr',
        'mail',
    ],
    'data': [
        # Seguridad
        'security/amunet_competencias_security.xml',
        'security/ir.model.access.csv',

        # Datos maestros
        'data/ir_sequence_data.xml',
        'data/res_config_params.xml',

        # Wizard (hereda el de amunet_quality, sin vista propia)
        # No se necesita XML adicional para el hook

        # Vistas
        'views/amunet_registro_capacitacion_views.xml',
        'views/amunet_matriz_competencias_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
