# -*- coding: utf-8 -*-
"""
Migration: blindar xmlids de grupos dinámicos contra DELETE en `-u all`.

Los grupos `group_warehouse_access_user_<uid>` se crean en runtime cuando un
usuario recibe acceso a un almacén. Sin `noupdate=True`, Odoo intenta borrar
sus xmlids durante el `-u all` (porque no aparecen en el XML del módulo), y
falla por FK contra `rule_group_rel`. Esta migración:

1. Setea `noupdate=True` en los xmlids existentes, para que Odoo los respete
   en futuros `-u`.
2. Elimina (a falta de eso) cualquier xmlid huérfano cuyo grupo ya no exista.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        # Primera instalación, nada que migrar
        return

    # 1. Blindar todos los xmlids de grupos dinámicos con noupdate=True
    cr.execute("""
        UPDATE ir_model_data
        SET noupdate = TRUE
        WHERE module = 'amunet_warehouse_access'
          AND model  = 'res.groups'
          AND name LIKE 'group_warehouse_access_user_%'
          AND noupdate IS NOT TRUE
    """)
    n_protected = cr.rowcount
    _logger.info("pre-migration 19.0.1.0.1: %s xmlids de grupos dinámicos blindados (noupdate=True)", n_protected)

    # 2. Eliminar xmlids cuyo grupo ya no existe en res.groups
    cr.execute("""
        DELETE FROM ir_model_data d
        WHERE d.module = 'amunet_warehouse_access'
          AND d.model  = 'res.groups'
          AND d.name LIKE 'group_warehouse_access_user_%'
          AND NOT EXISTS (
              SELECT 1 FROM res_groups g WHERE g.id = d.res_id
          )
    """)
    n_orphan = cr.rowcount
    _logger.info("pre-migration 19.0.1.0.1: %s xmlids huérfanos eliminados", n_orphan)
