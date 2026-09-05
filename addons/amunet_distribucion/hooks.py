# -*- coding: utf-8 -*-
"""Alta idempotente de la categoria raiz 'Distribucion'.

La categoria puede existir ya, creada a mano antes de que el modulo tuviera
este gancho (asi se hizo en staging el 24-ago-2026). En ese caso NO se crea
otra: se adopta la existente asignandole el xmlid del modulo, para que a
partir de aqui el arbol de categorias sea reproducible en cualquier base.
"""
import logging

_logger = logging.getLogger(__name__)

XMLID = 'amunet_distribucion.product_category_distribucion'
NOMBRE = 'Distribucion'


def post_init_hook(env):
    if env.ref(XMLID, raise_if_not_found=False):
        return
    Categoria = env['product.category']
    categoria = Categoria.search(
        [('name', '=', NOMBRE), ('parent_id', '=', False)], limit=1)
    if categoria:
        _logger.info("Distribucion: se adopta la categoria existente id=%s",
                     categoria.id)
    else:
        categoria = Categoria.create({'name': NOMBRE})
        _logger.info("Distribucion: categoria raiz creada id=%s", categoria.id)
    env['ir.model.data']._update_xmlids([{
        'xml_id': XMLID,
        'record': categoria,
        'noupdate': True,
    }])
