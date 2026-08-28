# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Devoluciones por cancelacion',
    'version': '19.0.1.0.0',
    'summary': 'Recepcion en almacen y reevaluacion por calidad del material que '
               'regresa de un pedido cancelado.',
    'description': """Circuito de devoluciones de producto terminado.

Cuando se cancela un pedido en la tienda, quien cancela contesta que paso con el
material. Si hay devolucion, aqui continua:

  1. Llega a Odoo la devolucion abierta en la tienda.
  2. Almacen confirma que recibio, y cuanto recibio de verdad. La mercancia
     entra a una ubicacion de cuarentena, que no es vendible.
  3. Calidad la reevalua y firma: libera todo, libera una parte, o la rechaza.
  4. Lo liberado vuelve al anaquel que le toca HOY, no al que tenia. Si el lote
     ya entro a caducidad corta mientras estaba fuera, vuelve como caducidad
     corta.

El material nunca deja de estar en algun lado, y cada paso tiene nombre y fecha.
Es lo que pide ISO 13485 de un producto sanitario que salio de la empresa y
regresa.""",
    'author': 'Amunet',
    'category': 'Inventory',
    'depends': ['stock', 'product_expiry', 'amunet_caducidad_alerta'],
    'data': [
        'security/ir.model.access.csv',
        'views/amunet_devolucion_views.xml',
        'data/ir_cron.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
