# -*- coding: utf-8 -*-
{
    'name': 'Amunet — Restricción de API Keys',
    'version': '19.0.1.0.0',
    'summary': 'Solo el líder del proyecto (fernando.ruiz) puede generar API keys',
    'description': """
Bloquea la generación de API keys (claves de integración / RPC) en Odoo a cualquier usuario
que no sea el líder del proyecto (fernando.ruiz), incluidos otros administradores.
Los procesos de backend en superusuario (sudo) siguen permitidos para tareas controladas.
""",
    'author': 'Amunet',
    'category': 'Tools',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [],
    'installable': True,
    'application': False,
}
