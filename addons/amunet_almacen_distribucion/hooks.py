# -*- coding: utf-8 -*-
"""Crea el almacen ADT y sus ubicaciones al instalar.

Se hace por codigo y no por datos XML porque los almacenes de esta instalacion
se crearon a mano y no tienen identificador de modulo: no hay a que referirse
desde un XML. Ademas Odoo genera solo las ubicaciones y tipos de operacion
basicos al crear un stock.warehouse, y aqui solo se agregan los propios de
Distribucion.

Es idempotente: si el almacen ya existe, no lo duplica.
"""

import logging

_logger = logging.getLogger(__name__)

CODIGO = 'ADT'
NOMBRE = 'Almacen de Distribucion'

# Ubicaciones propias de Distribucion, ademas de las que Odoo crea solo.
# Se separan a proposito: material recien llegado no es material vendible.
UBICACIONES = [
    ('Entrada', 'Llega aqui lo que traspasa la fabrica o lo que se compra, '
                'antes de contarlo'),
    ('Devoluciones', 'Producto que regresa de un cliente, en lo que se evalua'),
    ('Retenidos', 'Producto que no se puede vender: caducidad corta, dano, '
                  'pendiente de decision'),
]


def post_init_hook(env):
    Warehouse = env['stock.warehouse'].sudo()
    almacen = Warehouse.search([('code', '=', CODIGO)], limit=1)
    if almacen:
        _logger.info('ADT ya existe (id %s); no se crea de nuevo', almacen.id)
    else:
        almacen = Warehouse.create({
            'name': NOMBRE,
            'code': CODIGO,
            'reception_steps': 'one_step',
            'delivery_steps': 'ship_only',
        })
        _logger.info('Almacen ADT creado (id %s)', almacen.id)

    Location = env['stock.location'].sudo()
    vista = almacen.view_location_id
    for nombre, nota in UBICACIONES:
        ya = Location.search([
            ('location_id', '=', vista.id), ('name', '=', nombre),
        ], limit=1)
        if ya:
            continue
        # stock.location no tiene campo de comentario en Odoo 19; la nota
        # queda aqui en el codigo, que es donde se consulta el porque.
        Location.create({
            'name': nombre,
            'location_id': vista.id,
            'usage': 'internal',
        })
        _logger.info('Ubicacion ADT/%s creada', nombre)
    return True
