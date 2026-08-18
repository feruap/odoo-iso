# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import AccessError, UserError
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
            picking._amunet_check_origen_destino_iguales()

        return super().button_validate()

    def _amunet_check_origen_destino_iguales(self):
        """Bloquea validar un traslado interno cuando una línea de operación
        mueve el material al MISMO lugar de donde salió (origen = destino).

        Es un error de captura frecuente: al hacer un traslado entre almacenes
        (ej. Burgos -> Fábrica) el encabezado se cambia bien, pero la línea de
        operación conserva el destino por defecto (el mismo del origen), y el
        material no se mueve (traslado en falso). Este candado lo cacha antes
        de que quede 'hecho'.
        """
        self.ensure_one()
        if self.picking_type_code != 'internal':
            return
        malas = self.move_line_ids.filtered(
            lambda ml: ml.quantity and ml.location_id == ml.location_dest_id)
        if not malas:
            return
        detalle = '\n'.join(
            '- %s: %s -> %s' % (
                ml.product_id.default_code or ml.product_id.display_name,
                ml.location_id.complete_name, ml.location_dest_id.complete_name)
            for ml in malas[:8])
        raise UserError(_(
            'No se puede validar este traslado: hay líneas cuyo DESTINO es el '
            'MISMO que el origen, así que el material no se movería.\n\n'
            'Corrige el destino de la operación al almacén/ubicación correcto '
            '(ej. AMP/Existencias para Fábrica) y vuelve a validar.\n\n%s'
        ) % detalle)

    @api.model_create_multi
    def create(self, vals_list):
        """Override para validar acceso al crear picking.

        Migrado a @api.model_create_multi (Odoo 18+) el 2026-05-09 para que
        la validacion de acceso por almacen se aplique tambien en creaciones
        en batch (importaciones masivas, jobs, modulos que crean varios
        pickings de golpe). Antes con @api.model la firma singular podia
        ser bypasseada en esos casos.
        """
        # Crear primero para tener acceso a campos relacionados
        pickings = super().create(vals_list)

        # Validar acceso para cada picking creado
        for picking in pickings:
            picking._check_warehouse_access_permission(operation='crear')

        return pickings

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
                    operation='modificar'
                )

        return super().write(vals)

    def unlink(self):
        """Override para validar acceso al eliminar picking."""
        # Validar acceso antes de eliminar
        for picking in self:
            picking._check_warehouse_access_permission(
                operation='eliminar'
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
