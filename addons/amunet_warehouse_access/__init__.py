# -*- coding: utf-8 -*-

from . import models


def pre_init_hook(cr):
    """
    Hook que se ejecuta ANTES de instalar/actualizar el módulo.
    
    Limpia registros dinámicos (reglas y grupos) para evitar errores de
    restricciones de clave foránea durante la actualización.
    """
    import logging
    _logger = logging.getLogger(__name__)
    
    try:
        # Limpiar reglas ir.rule asociadas a grupos dinámicos
        cr.execute("""
            DELETE FROM ir_rule 
            WHERE id IN (
                SELECT DISTINCT rgr.rule_group_id
                FROM rule_group_rel rgr
                INNER JOIN res_groups rg ON rgr.group_id = rg.id
                INNER JOIN ir_model_data imd ON imd.res_id = rg.id 
                    AND imd.model = 'res.groups'
                    AND imd.module = 'amunet_warehouse_access'
                    AND imd.name LIKE 'group_warehouse_access_user_%'
            )
        """)
        rules_deleted = cr.rowcount
        if rules_deleted > 0:
            _logger.info(f"Pre-init: Eliminadas {rules_deleted} reglas ir.rule asociadas a grupos dinámicos")
        
        # Desasociar usuarios de grupos dinámicos
        cr.execute("""
            DELETE FROM res_groups_users_rel
            WHERE gid IN (
                SELECT rg.id
                FROM res_groups rg
                INNER JOIN ir_model_data imd ON imd.res_id = rg.id 
                    AND imd.model = 'res.groups'
                    AND imd.module = 'amunet_warehouse_access'
                    AND imd.name LIKE 'group_warehouse_access_user_%'
            )
        """)
        users_unlinked = cr.rowcount
        if users_unlinked > 0:
            _logger.info(f"Pre-init: Desasociados {users_unlinked} usuarios de grupos dinámicos")
        
        # Eliminar grupos dinámicos
        cr.execute("""
            DELETE FROM res_groups
            WHERE id IN (
                SELECT rg.id
                FROM res_groups rg
                INNER JOIN ir_model_data imd ON imd.res_id = rg.id 
                    AND imd.model = 'res.groups'
                    AND imd.module = 'amunet_warehouse_access'
                    AND imd.name LIKE 'group_warehouse_access_user_%'
            )
        """)
        groups_deleted = cr.rowcount
        if groups_deleted > 0:
            _logger.info(f"Pre-init: Eliminados {groups_deleted} grupos dinámicos")
        
        # Limpiar XML IDs huérfanos
        cr.execute("""
            DELETE FROM ir_model_data
            WHERE module = 'amunet_warehouse_access'
            AND model = 'res.groups'
            AND name LIKE 'group_warehouse_access_user_%'
        """)
        xml_ids_deleted = cr.rowcount
        if xml_ids_deleted > 0:
            _logger.info(f"Pre-init: Eliminados {xml_ids_deleted} XML IDs huérfanos")
            
    except Exception as e:
        _logger.warning(f"Error en pre_init_hook (continuando): {e}")


def post_init_hook(cr, registry):
    """
    Hook que se ejecuta después de instalar/actualizar el módulo.
    
    Crea las reglas de visibilidad de forma segura, verificando que los modelos existan.
    """
    from odoo import api, SUPERUSER_ID
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    try:
        # Verificar que el modelo existe antes de llamar al método
        if 'amunet.warehouse.access' in env:
            env['amunet.warehouse.access']._init_visibility_rules()
    except Exception as e:
        import logging
        _logger = logging.getLogger(__name__)
        _logger.warning(f"Error inicializando reglas de visibilidad: {e}")
