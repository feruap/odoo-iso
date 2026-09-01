# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Requisicion de compra desde el plan',
    'version': '19.0.1.0.0',
    'summary': 'Boton para crear ordenes de compra (sin precio) desde los '
               'faltantes de materia prima del plan de produccion sugerido. '
               'Agrupa por proveedor; los que se fabrican (sin proveedor) los '
               'reporta aparte, no los mete a compra.',
    'author': 'Amunet - Agente PM',
    'depends': ['amunet_production_plan', 'purchase'],
    'data': [
        'views/production_plan_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
