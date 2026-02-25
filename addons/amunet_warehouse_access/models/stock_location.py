# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)


class StockLocation(models.Model):
    """
    Extensión de stock.location para validar accesos a almacenes.

    Agrega validaciones en:
    - create: Verificar acceso al crear ubicación
    - write: Verificar acceso al modificar ubicación

    Epic-033: Control de Acceso Dinámico por Almacén
    """
    _inherit = 'stock.location'

    # ========== OVERRIDE METHODS ==========

    @api.model
    def create(self, vals):
        """Override para validar acceso al crear ubicación."""
        # Crear primero para tener acceso a campos relacionados
        location = super().create(vals)

        # Validar acceso después de creación
        location._check_warehouse_access_permission(operation='crear', raise_warning=False)

        return location

    def write(self, vals):
        """Override para validar acceso al modificar ubicación."""
        # Validar acceso antes de modificar
        critical_fields = {'warehouse_id', 'location_id', 'active'}

        if any(field in vals for field in critical_fields):
            for location in self:
                location._check_warehouse_access_permission(
                    operation='modificar',
                    raise_warning=False
                )

        return super().write(vals)

    def unlink(self):
        """Override para validar acceso al eliminar ubicación."""
        # Validar acceso antes de eliminar
        for location in self:
            location._check_warehouse_access_permission(
                operation='eliminar',
                raise_warning=False
            )

        return super().unlink()

    # ========== VALIDATION METHODS ==========

    def _check_warehouse_access_permission(self, operation='acceder', raise_warning=True):
        """
        Validar que el usuario tenga permiso para operar en el almacén de la ubicación.

        :param operation: str - Operación que se intenta realizar
        :param raise_warning: bool - Si True, lanza AccessError en caso de no tener permiso
        :raises: AccessError si el usuario no tiene permiso
        """
        self.ensure_one()

        # Bypass para administradores
        if self.env.user.has_group('base.group_system'):
            return True

        # Bypass para operaciones del sistema (sudo, cron, etc.)
        if self.env.su:
            return True

        # Obtener almacén de la ubicación
        warehouse = self.warehouse_id

        if not warehouse:
            # Ubicaciones sin almacén (vistas, virtuales, etc.) no se validan
            return True

        # Validar acceso usando método del modelo de acceso
        try:
            self.env['amunet.warehouse.access']._check_warehouse_access(
                user=self.env.user,
                warehouse=warehouse,
                operation_type=None,  # No hay tipo de operación específico para ubicaciones
                raise_exception=True
            )
            return True

        except AccessError as e:
            if raise_warning:
                raise AccessError(
                    f"No tiene permiso para {operation} la ubicación '{self.complete_name}'.\n\n"
                    f"Detalles:\n"
                    f"- Almacén: {warehouse.name}\n\n"
                    f"{str(e)}"
                )
            else:
                _logger.warning(
                    f"Usuario '{self.env.user.name}' intentó {operation} ubicación "
                    f"'{self.complete_name}' sin permisos suficientes: {str(e)}"
                )
                return False
