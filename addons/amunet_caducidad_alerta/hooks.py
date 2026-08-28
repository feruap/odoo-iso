# -*- coding: utf-8 -*-
"""Alta idempotente de las ubicaciones fisicas de promociones.

En el almacen, la mercancia de caducidad corta y la de cortesias van en
anaqueles distintos. Odoo no tenia esas ubicaciones, asi que el sistema no
podia decir donde estaba realmente cada lote. Aqui se crean, colgando del
almacen de producto terminado.
"""
import logging

_logger = logging.getLogger(__name__)

UBICACIONES = [
    ('amunet_caducidad_alerta.location_caducidad_corta', 'Caducidad corta'),
    ('amunet_caducidad_alerta.location_cortesias', 'Cortesias'),
]


def _padre_apt(env):
    """La ubicacion vista del almacen de producto terminado."""
    almacen = env['stock.warehouse'].search([('code', '=', 'APT')], limit=1)
    if almacen and almacen.view_location_id:
        return almacen.view_location_id
    return env['stock.location'].search(
        [('complete_name', '=', 'APT'), ('usage', '=', 'view')], limit=1)


def post_init_hook(env):
    padre = _padre_apt(env)
    if not padre:
        _logger.warning('Caducidad: no se encontro el almacen APT; '
                        'las ubicaciones de promociones no se crearon.')
        return

    Ubicacion = env['stock.location']
    for xmlid, nombre in UBICACIONES:
        if env.ref(xmlid, raise_if_not_found=False):
            continue
        ubicacion = Ubicacion.search([
            ('name', '=', nombre), ('location_id', '=', padre.id),
        ], limit=1)
        if ubicacion:
            _logger.info('Caducidad: se adopta la ubicacion existente %s (id=%s)',
                         nombre, ubicacion.id)
        else:
            ubicacion = Ubicacion.create({
                'name': nombre,
                'location_id': padre.id,
                'usage': 'internal',
                'company_id': padre.company_id.id or env.company.id,
            })
            _logger.info('Caducidad: ubicacion %s creada (id=%s)', nombre, ubicacion.id)
        env['ir.model.data']._update_xmlids([{
            'xml_id': xmlid,
            'record': ubicacion,
            'noupdate': True,
        }])
