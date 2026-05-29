# -*- coding: utf-8 -*-

from . import models


def pre_init_hook(env):
    """
    Hook ANTES de actualizar el módulo.

    Solo elimina los xmlids (`ir_model_data`) de los grupos dinámicos por usuario
    para que Odoo no intente borrarlos durante el `-u all` (lo cual fallaría por
    FK con `rule_group_rel`). Los grupos y reglas siguen vivos; quedan como
    permisos no administrados por Odoo. El módulo los volverá a registrar con
    noupdate=True cuando los use.
    """
    import logging
    _logger = logging.getLogger(__name__)
    try:
        # Adaptar para Odoo 19 (env) y antiguos (cr): obtener cursor
        cr = env if hasattr(env, 'execute') else env.cr
        cr.execute("""
            DELETE FROM ir_model_data
            WHERE module = 'amunet_warehouse_access'
              AND model = 'res.groups'
              AND name LIKE 'group_warehouse_access_user_%'
        """)
        _logger.info(f"pre_init_hook: xmlids huerfanos eliminados ({cr.rowcount})")
    except Exception as e:
        _logger.warning(f"pre_init_hook (continuando): {e}")


def post_init_hook(env):
    """Inicializa reglas globales de visibilidad si los modelos existen."""
    import logging
    _logger = logging.getLogger(__name__)
    try:
        # Compat con firmas (cr, registry) y (env)
        if hasattr(env, 'cr'):
            _env = env
        else:
            from odoo import api, SUPERUSER_ID
            _env = api.Environment(env, SUPERUSER_ID, {})
        if 'amunet.warehouse.access' in _env:
            _env['amunet.warehouse.access']._init_visibility_rules()
    except Exception as e:
        _logger.warning(f"post_init_hook: {e}")
