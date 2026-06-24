# -*- coding: utf-8 -*-
from . import models
from . import wizard
from . import controllers


def _amunet_limpieza_post_init(env):
    """Siembra los ítems de limpieza por área según su perfil (almacén o estándar)."""
    env['amunet.limpieza.item']._amunet_seed_items()
