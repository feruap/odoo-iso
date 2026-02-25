# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    """
    Extensión de stock.picking para validar accesos a almacenes.

    Agrega validaciones en:
    - action_confirm: Verificar acceso antes de confirmar
    - button_validate: Verificar acceso antes de validar

    Epic-033: Control de Acceso Dinámico por Almacén
    """
    _inherit = 'stock.picking'

    # ========== OVERRIDE METHODS ==========

    def action_confirm(self):
        """Override para validar acceso antes de confirmar picking."""
        # Validar acceso ANTES de confirmar
        for picking in self:
            picking._check_warehouse_access_permission(operation='confirmar')

        return super().action_confirm()

    def button_validate(self):
        """Override para validar acceso antes de validar picking."""
        # Validar acceso ANTES de validar
        for picking in self:
            picking._check_warehouse_access_permission(operation='validar')

        return super().button_validate()

    @api.model
    def create(self, vals):
        """Override para validar acceso al crear picking."""
        # Crear primero para tener acceso a campos relacionados
        picking = super().create(vals)

        # Validar acceso después de creación
        picking._check_warehouse_access_permission(operation='crear', raise_warning=False)

        return picking

    def write(self, vals):
        """Override para validar acceso al modificar picking."""
        # Validar acceso antes de modificar
        critical_fields = {
            'picking_type_id', 'location_id', 'location_dest_id',
            'move_ids_without_package', 'move_line_ids_without_package'
        }

        if any(field in vals for field in critical_fields):
            for picking in self:
                picking._check_warehouse_access_permission(
                    operation='modificar',
                    raise_warning=False
                )

        return super().write(vals)

    def unlink(self):
        """Override para validar acceso al eliminar picking."""
        # Validar acceso antes de eliminar
        for picking in self:
            picking._check_warehouse_access_permission(
                operation='eliminar',
                raise_warning=False
            )

        return super().unlink()

    # ========== VALIDATION METHODS ==========

    def _check_warehouse_access_permission(self, operation='acceder', raise_warning=True):
        """
        Validar que el usuario tenga permiso para operar en el almacén del picking.

        :param operation: str - Operación que se intenta realizar (confirmar, validar, etc.)
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

        # Obtener almacén del picking
        warehouse = self.picking_type_id.warehouse_id

        if not warehouse:
            _logger.warning(
                f"Picking {self.name} (ID: {self.id}) no tiene almacén asociado. "
                f"No se puede validar acceso."
            )
            return True

        # Validar acceso usando método del modelo de acceso
        try:
            self.env['amunet.warehouse.access']._check_warehouse_access(
                user=self.env.user,
                warehouse=warehouse,
                operation_type=self.picking_type_id,
                raise_exception=True
            )
            return True

        except AccessError as e:
            if raise_warning:
                # Re-lanzar excepción con contexto adicional
                raise AccessError(
                    f"No tiene permiso para {operation} la operación '{self.name}'.\n\n"
                    f"Detalles:\n"
                    f"- Operación: {self.picking_type_id.name}\n"
                    f"- Almacén: {warehouse.name}\n\n"
                    f"{str(e)}"
                )
            else:
                _logger.warning(
                    f"Usuario '{self.env.user.name}' intentó {operation} picking "
                    f"'{self.name}' sin permisos suficientes: {str(e)}"
                )
                return False
