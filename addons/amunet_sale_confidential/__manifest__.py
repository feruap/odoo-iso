# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Ventas confidenciales',
    'summary': 'Restringe el acceso a pedidos de venta y oculta todo importe comercial.',
    'description': """
Extiende la politica de amunet_price_visibility al modulo de Ventas.

Por que existe
--------------
La demanda historica es necesaria para planear produccion, pero la informacion
comercial (precios de venta, importes, margenes) es confidencial de Direccion.
Este modulo separa ambas cosas: las CANTIDADES quedan disponibles para planear,
los IMPORTES no existen para quien no esta autorizado.

Controles
---------
1. Grupo `Amunet / Ventas confidencial`: unico que ve el menu Ventas. Implica el
   grupo de vendedor de Odoo. Al instalar se otorga automaticamente a quien ya
   tenia el rol de administrador de Ventas.
2. Campos de dinero de sale.order, sale.order.line y sale.report redefinidos con
   `groups=amunet_price_visibility.group_price_viewer`. A nivel ORM: quien no
   tiene el grupo no puede leerlos, filtrarlos, agruparlos, exportarlos ni
   consultarlos por API o XML-RPC. No es un ocultamiento visual.
3. `read()` enmascara y `export_data()` lanza AccessError, mismo patron que
   amunet_price_visibility, por si un cliente externo pide los campos a mano.

Lo que SI queda visible para planeacion (sin dinero): producto, cantidad, fecha
y estado del pedido.
    """,
    'author': 'Amunet',
    'category': 'Hidden',
    'version': '19.0.1.0.0',
    'depends': [
        'sale',
        'sale_management',
        'sale_stock',
        'amunet_price_visibility',
    ],
    'data': [
        'security/security.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
