# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Tablero de compras',
    'summary': 'Una sola pantalla con todo el circuito de compras: que falta '
               'autorizar, que falta comprar, que va en camino, que esta '
               'atrasado y que ya llego.',
    'author': 'Amunet',
    'category': 'Inventory/Purchase',
    'version': '19.0.1.0.0',
    # El tablero es solo lectura: junta en una pantalla lo que hoy esta
    # repartido entre Compras (OC) y el Marketplace Interno (SC).
    # Unico campo nuevo: la via que prefiere el solicitante (avion / barco),
    # que es solo una preferencia; la via final la decide Compras.
    'depends': ['amunet_compras_general'],
    'data': [
        'views/tablero_views.xml',
        'views/via_preferida_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'amunet_compras_tablero/static/src/scss/tablero.scss',
            'amunet_compras_tablero/static/src/js/tablero.js',
            'amunet_compras_tablero/static/src/xml/tablero.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
