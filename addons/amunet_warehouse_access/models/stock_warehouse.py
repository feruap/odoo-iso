# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class StockWarehouse(models.Model):
    """
    Extensión de stock.warehouse para gestionar usuarios con acceso.

    Agrega campos para:
    - Configuraciones de acceso de usuarios (One2many)
    - Usuarios con acceso (Many2many computed)

    Epic-033: Control de Acceso Dinámico por Almacén
    """
    _inherit = 'stock.warehouse'

    # ========== FIELDS ==========

    user_access_ids = fields.One2many(
        comodel_name='amunet.warehouse.access',
        inverse_name='warehouse_id',
        string='Configuraciones de acceso',
        help="Configuración de usuarios y operaciones permitidas en este almacén."
    )

    allowed_user_ids = fields.Many2many(
        comodel_name='res.users',
        string='Usuarios permitidos',
        compute='_compute_allowed_user_ids',
        store=False,
        help="Usuarios que tienen acceso a este almacén (calculado automáticamente)."
    )

    allowed_user_count = fields.Integer(
        string='Contador de usuarios',
        compute='_compute_allowed_user_count',
        help="Número de usuarios con acceso a este almacén."
    )

    # ========== COMPUTED FIELDS ==========

    @api.depends('user_access_ids', 'user_access_ids.user_id', 'user_access_ids.active')
    def _compute_allowed_user_ids(self):
        """Calcular usuarios permitidos desde configuraciones activas."""
        for warehouse in self:
            # Solo accesos activos
            active_accesses = warehouse.user_access_ids.filtered(lambda a: a.active)
            warehouse.allowed_user_ids = active_accesses.mapped('user_id')

    @api.depends('allowed_user_ids')
    def _compute_allowed_user_count(self):
        """Contar usuarios con acceso."""
        for warehouse in self:
            warehouse.allowed_user_count = len(warehouse.allowed_user_ids)

    # ========== HELPER METHODS ==========

    def get_users_with_access(self, operation_type=None):
        """
        Obtener usuarios que tienen acceso a este almacén.

        :param operation_type: stock.picking.type record (opcional, filtrar por operación)
        :return: res.users recordset
        """
        self.ensure_one()

        # Filtrar accesos activos
        accesses = self.user_access_ids.filtered(lambda a: a.active)

        if operation_type:
            # Filtrar por operación específica
            accesses = accesses.filtered(
                lambda a: (
                    a.access_type == 'full' or
                    operation_type in a.operation_type_ids
                )
            )

        return accesses.mapped('user_id')

    def user_has_access(self, user, operation_type=None):
        """
        Verificar si un usuario tiene acceso a este almacén.

        :param user: res.users record
        :param operation_type: stock.picking.type record (opcional)
        :return: Boolean
        """
        self.ensure_one()

        # Bypass para administradores
        if user.has_group('base.group_system'):
            return True

        # Usar método del modelo de acceso
        return self.env['amunet.warehouse.access']._check_warehouse_access(
            user=user,
            warehouse=self,
            operation_type=operation_type,
            raise_exception=False
        )

    # ========== ACTIONS ==========

    def action_view_user_accesses(self):
        """Acción para ver usuarios con acceso a este almacén."""
        self.ensure_one()

        return {
            'name': f'Usuarios con Acceso: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.warehouse.access',
            'view_mode': 'list,form',
            'domain': [('warehouse_id', '=', self.id)],
            'context': {'default_warehouse_id': self.id},
        }
