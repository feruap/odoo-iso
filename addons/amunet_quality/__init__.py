# -*- coding: utf-8 -*-

from . import controllers
from . import models
from . import wizard

def post_init_hook(env):
    """
    Hook para cargar vistas puente de Enterprise solo si los módulos están presentes.
    Esto permite que el módulo sea 'Hybrid' (Community + Enterprise).
    """
    from odoo.tools import convert_file
    import os
    
    # 1. Puente de Tecnovigilancia (Helpdesk Enterprise)
    helpdesk = env['ir.module.module'].search([('name', '=', 'helpdesk'), ('state', '=', 'installed')])
    if helpdesk:
        manifest_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '__manifest__.py'))
        view_path = os.path.join(os.path.dirname(__file__), 'views', 'amunet_quality_helpdesk_views.xml')
        if os.path.exists(view_path):
            convert_file(env.cr, 'amunet_quality', 'views/amunet_quality_helpdesk_views.xml', {}, 'init', True, 'data', view_path)

