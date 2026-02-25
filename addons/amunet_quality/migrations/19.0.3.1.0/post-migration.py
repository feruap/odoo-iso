# -*- coding: utf-8 -*-
"""
Migración 19.0.3.1.0: Eliminación del campo parameter_type

Este script elimina las columnas parameter_type de las tablas relacionadas
con parámetros de calidad, ya que este campo era redundante (la información
está en evaluation_type de cada especificación).

Refactorización: feature/034-refactor
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Elimina columnas relacionadas con parameter_type que fueron stored.

    Args:
        cr: Database cursor
        version: Module version being installed
    """
    _logger.info("=== Iniciando migración 19.0.3.1.0: Eliminación de parameter_type ===")

    # Lista de tablas y columnas a eliminar
    tables_to_clean = [
        ('amunet_quality_check_parameter', 'parameter_type'),
        ('amunet_quality_parameter_product_rel', 'parameter_type'),
        ('amunet_quality_test_line', 'parameter_type'),
    ]

    for table_name, column_name in tables_to_clean:
        try:
            # Verificar si la columna existe antes de intentar eliminarla
            cr.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
            """, (table_name, column_name))

            if cr.fetchone():
                _logger.info(f"Eliminando columna {column_name} de tabla {table_name}")
                cr.execute(f"""
                    ALTER TABLE {table_name}
                    DROP COLUMN IF EXISTS {column_name} CASCADE
                """)
                _logger.info(f"✓ Columna {column_name} eliminada de {table_name}")
            else:
                _logger.info(f"→ Columna {column_name} no existe en {table_name}, omitiendo")

        except Exception as e:
            _logger.error(f"✗ Error eliminando columna {column_name} de {table_name}: {e}")
            # No hacer raise para permitir que la migración continúe
            # En el peor caso, la columna quedará huérfana pero no afectará funcionalidad

    _logger.info("=== Migración 19.0.3.1.0 completada ===")
