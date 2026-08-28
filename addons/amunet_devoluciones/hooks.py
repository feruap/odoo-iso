# -*- coding: utf-8 -*-
"""Alta idempotente del anaquel de cuarentena.

El material devuelto no puede volver al anaquel de siempre nada mas llegar:
estuvo fuera de la empresa y nadie sabe como lo trataron. Necesita un lugar
propio, visible y contable, donde exista pero no se venda.
"""
import logging

_logger = logging.getLogger(__name__)

XMLID = 'amunet_devoluciones.location_devoluciones'
NOMBRE = 'Devoluciones por evaluar'


def post_init_hook(env):
    if env.ref(XMLID, raise_if_not_found=False):
        return
    almacen = env['stock.warehouse'].search([('code', '=', 'APT')], limit=1)
    padre = almacen.view_location_id if almacen else False
    if not padre:
        _logger.warning('Devoluciones: no se encontro el almacen APT; '
                        'la ubicacion de cuarentena no se creo.')
        return

    Ubicacion = env['stock.location']
    ubicacion = Ubicacion.search([
        ('name', '=', NOMBRE), ('location_id', '=', padre.id),
    ], limit=1)
    if ubicacion:
        _logger.info('Devoluciones: se adopta la ubicacion existente (id=%s)', ubicacion.id)
    else:
        ubicacion = Ubicacion.create({
            'name': NOMBRE,
            'location_id': padre.id,
            'usage': 'internal',
            'company_id': padre.company_id.id or env.company.id,
        })
        _logger.info('Devoluciones: ubicacion creada (id=%s)', ubicacion.id)
    env['ir.model.data']._update_xmlids([{
        'xml_id': XMLID, 'record': ubicacion, 'noupdate': True,
    }])
