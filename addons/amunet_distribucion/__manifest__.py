# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Distribucion (clasificador raiz)',
    'version': '19.0.2.0.0',
    'summary': 'Bloquea que un producto vendible sin lista de materiales (no se '
               'fabrica) quede en "Producto terminado"; debe ir en "Distribucion". '
               'Segrega compra-venta de fabricacion desde la raiz.',
    'author': 'Amunet - Agente PM',
    'depends': ['mrp'],
    'data': [],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
