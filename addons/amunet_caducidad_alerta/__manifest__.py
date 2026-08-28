# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Semaforo de caducidad en lotes',
    'version': '19.0.3.0.0',
    'summary': 'Marca cada lote como normal, caducidad corta, cortesia o retirar, '
               'para que almacen sepa que mover a promociones y cuando.',
    'description': """Semaforo de caducidad para el almacen de producto terminado.

Calcula, para cada lote con fecha de caducidad, en que condicion comercial esta:

  * Normal          - le quedan mas de 6 meses
  * Caducidad corta - entre 4 y 6 meses (se vende con descuento)
  * Cortesia        - entre 2 y 4 meses (se vende a precio simbolico)
  * Retirar         - menos de 2 meses, ya no se pone a la venta
  * Vencido         - la fecha ya paso

Los umbrales se ajustan en Ajustes tecnicos sin tocar codigo. Un proceso diario
recalcula la condicion de todos los lotes, porque el paso del tiempo la cambia
aunque nadie edite nada.

Ademas registra donde esta fisicamente cada lote -anaquel normal, caducidad
corta, cortesias o retenidos- y avisa cuales estan fuera de su lugar. Desde la
lista de pendientes, almacen confirma el movimiento y Odoo genera el traslado
interno correspondiente, con folio, fecha y usuario.""",
    'author': 'Amunet',
    'category': 'Inventory',
    'depends': ['stock', 'product_expiry'],
    'data': [
        'security/ir.model.access.csv',
        'data/parametros.xml',
        'data/ir_cron.xml',
        'wizard/amunet_movimiento_caducidad_views.xml',
        'views/stock_lot_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
