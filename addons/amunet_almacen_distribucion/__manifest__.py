# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Almacen de Distribucion',
    'version': '19.0.1.0.1',
    'summary': 'Almacen ADT y aplicacion propia para Distribucion, separada de '
               'la Fabrica',
    'description': """
Almacen de Distribucion (ADT)
=============================

Amunet tiene DOS operaciones distintas sobre el mismo inventario:

- La **fabrica**, que produce y guarda en APT (Almacen de Producto Terminado).
- **Distribucion**, que vende: recibe de la fabrica, ademas compra por su
  cuenta, y es de donde sale lo que se publica en la tienda.

Este modulo le da a Distribucion su propio almacen (ADT) y su propia
aplicacion, con sus pantallas y sus accesos. Quien trabaja en Distribucion ve
solo lo suyo.

NO se duplica el modulo de Inventario: eso partiria las existencias en dos
sistemas que no se hablan y se perderia la trazabilidad de un producto que pasa
de fabrica a venta. Se reusa el inventario de Odoo, filtrado a este almacen.

Los dos caminos de entrada:
  - Traspaso desde APT, con documento: la fabrica entrega, Distribucion recibe.
  - Compra propia, que llega directo a ADT sin pasar por fabrica.
""",
    'author': 'Amunet - Agente PM',
    'category': 'Inventory',
    'license': 'LGPL-3',
    'depends': ['stock', 'purchase', 'amunet_warehouse_access'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/menus.xml',
        'views/stock_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
    'auto_install': False,
}
