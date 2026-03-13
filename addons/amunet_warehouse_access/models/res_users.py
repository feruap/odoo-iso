# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    """
    Extensión de res.users para gestionar accesos a almacenes.

    Agrega campos para:
    - Configuraciones de acceso a almacenes (One2many)
    - Almacenes permitidos (Many2many computed)

    Epic-033: Control de Acceso Dinámico por Almacén
    """
    _inherit = 'res.users'

    # ========== FIELDS ==========

    warehouse_access_ids = fields.One2many(
        comodel_name='amunet.warehouse.access',
        inverse_name='user_id',
        string='Configuraciones de control de acceso',
        help="Configuración de almacenes y operaciones permitidas para este usuario."
    )

    warehouse_ids = fields.Many2many(
        comodel_name='stock.warehouse',
        string='Almacenes permitidos',
        compute='_compute_warehouse_ids',
        store=False,
        help="Almacenes a los que este usuario tiene acceso (calculado automáticamente)."
    )

    warehouse_count = fields.Integer(
        string='Almacenes',
        compute='_compute_warehouse_count',
        help="Número de almacenes a los que tiene acceso."
    )

    # ========== COMPUTED FIELDS ==========

    @api.depends('warehouse_access_ids', 'warehouse_access_ids.warehouse_id', 'warehouse_access_ids.active')
    def _compute_warehouse_ids(self):
        """Calcular almacenes permitidos desde configuraciones activas."""
        for user in self:
            # Solo accesos activos
            active_accesses = user.warehouse_access_ids.filtered(lambda a: a.active)
            user.warehouse_ids = active_accesses.mapped('warehouse_id')

    @api.depends('warehouse_ids')
    def _compute_warehouse_count(self):
        """Contar almacenes permitidos."""
        for user in self:
            user.warehouse_count = len(user.warehouse_ids)

    # ========== HELPER METHODS ==========

    def has_warehouse_access(self, warehouse, operation_type=None):
        """
        Verificar si el usuario tiene acceso a un almacén y operación específica.

        :param warehouse: stock.warehouse record
        :param operation_type: stock.picking.type record (opcional)
        :return: Boolean
        """
        self.ensure_one()

        # Bypass para administradores
        if self.has_group('base.group_system'):
            return True

        # Usar método del modelo de acceso
        return self.env['amunet.warehouse.access']._check_warehouse_access(
            user=self,
            warehouse=warehouse,
            operation_type=operation_type,
            raise_exception=False
        )

    def get_allowed_warehouses(self):
        """
        Obtener lista de almacenes permitidos para este usuario.

        :return: stock.warehouse recordset
        """
        self.ensure_one()

        # Bypass para administradores (todos los almacenes)
        if self.has_group('base.group_system'):
            return self.env['stock.warehouse'].search([])

        return self.warehouse_ids

    def get_allowed_operation_types(self, warehouse=None):
        """
        Obtener tipos de operación permitidos para este usuario.

        :param warehouse: stock.warehouse record (opcional, filtrar por almacén)
        :return: stock.picking.type recordset
        """
        self.ensure_one()

        # Bypass para administradores (todas las operaciones)
        if self.has_group('base.group_system'):
            domain = []
            if warehouse:
                domain = [('warehouse_id', '=', warehouse.id)]
            return self.env['stock.picking.type'].search(domain)

        # Filtrar accesos activos
        accesses = self.warehouse_access_ids.filtered(lambda a: a.active)

        if warehouse:
            accesses = accesses.filtered(lambda a: a.warehouse_id == warehouse)

        # Recopilar operaciones permitidas
        operation_types = self.env['stock.picking.type']

        for access in accesses:
            if access.access_type == 'full':
                # Acceso completo: todas las operaciones del almacén
                operation_types |= access.warehouse_id.pick_type_id
                operation_types |= access.warehouse_id.in_type_id
                operation_types |= access.warehouse_id.out_type_id
                operation_types |= access.warehouse_id.int_type_id
            elif access.access_type == 'restricted':
                # Acceso restringido: solo operaciones configuradas
                operation_types |= access.operation_type_ids

        return operation_types

    # ========== OVERRIDES ==========

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        self._assign_employee_filters(users)
        return users

    @api.model
    def _assign_employee_filters(self, users):
        """Asignar filtros favoritos de hr.employee a los usuarios dados."""
        filters = self.env['ir.filters'].sudo().search([
            ('model_id', '=', 'hr.employee'),
        ])
        for f in filters:
            f.sudo().write({'user_ids': [(4, u.id) for u in users]})

    # ========== ACTIONS ==========

    def action_view_warehouse_accesses(self):
        """Acción para ver accesos configurados del usuario."""
        self.ensure_one()

        return {
            'name': f'Accesos a almacenes: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.warehouse.access',
            'view_mode': 'list,form',
            'domain': [('user_id', '=', self.id)],
            'context': {'default_user_id': self.id},
        }
