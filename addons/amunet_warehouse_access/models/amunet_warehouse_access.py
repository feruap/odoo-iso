# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessError
import logging

_logger = logging.getLogger(__name__)


class AmunetWarehouseAccess(models.Model):
    """
    Configuración de acceso dinámico usuario-almacén-operación.

    Este modelo permite asignar almacenes específicos a usuarios y restringir
    qué operaciones pueden realizar. Genera automáticamente Record Rules de Odoo
    basadas en la configuración.

    Epic-033: Control de Acceso Dinámico por Almacén
    """
    _name = 'amunet.warehouse.access'
    _description = 'Control de Acceso a Almacenes'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'user_id, warehouse_id'

    # ========== FIELDS ==========

    name = fields.Char(
        string='Nombre',
        compute='_compute_name',
        store=True,
        index=True
    )

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Usuario',
        required=True,
        index=True,
        ondelete='cascade',
        tracking=True
    )

    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Almacén',
        required=True,
        index=True,
        ondelete='cascade',
        tracking=True
    )

    access_type = fields.Selection(
        selection=[
            ('full', 'Acceso completo'),
            ('restricted', 'Acceso restringido'),
        ],
        string='Tipo de acceso',
        required=True,
        default='full',
        tracking=True,
        help="Acceso Completo: El usuario puede realizar todas las operaciones en el almacén.\n"
             "Acceso Restringido: El usuario solo puede realizar operaciones específicas."
    )

    operation_type_ids = fields.Many2many(
        comodel_name='stock.picking.type',
        relation='amunet_warehouse_access_operation_rel',
        column1='access_id',
        column2='operation_type_id',
        string='Operaciones permitidas',
        domain="[('warehouse_id', '=', warehouse_id)]",
        tracking=True,
        help="Tipos de operación permitidos cuando el acceso es restringido."
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
        tracking=True,
        help="Desactivar temporalmente el acceso sin eliminarlo."
    )

    rule_ids = fields.One2many(
        comodel_name='amunet.warehouse.access.rule',
        inverse_name='access_id',
        string='Reglas generadas',
        readonly=True,
        help="Record rules de Odoo generadas automáticamente para este acceso."
    )

    rule_count = fields.Integer(
        string='Reglas',
        compute='_compute_rule_count'
    )

    # ========== CONSTRAINTS ==========

    @api.constrains('user_id', 'warehouse_id')
    def _check_user_warehouse_unique(self):
        """Validar que no haya accesos duplicados para usuario-almacén."""
        for record in self:
            existing = self.search([
                ('user_id', '=', record.user_id.id),
                ('warehouse_id', '=', record.warehouse_id.id),
                ('id', '!=', record.id),
            ], limit=1)
            if existing:
                raise ValidationError(
                    f"Este usuario ya tiene acceso configurado para este almacén. "
                    f"Edite el acceso existente en lugar de crear uno nuevo."
                )

    @api.constrains('access_type', 'operation_type_ids')
    def _check_restricted_has_operations(self):
        """Validar que acceso restringido tenga al menos una operación."""
        for record in self:
            if record.access_type == 'restricted' and not record.operation_type_ids:
                raise ValidationError(
                    f"El acceso restringido para el usuario '{record.user_id.name}' "
                    f"al almacén '{record.warehouse_id.name}' debe tener al menos "
                    f"una operación permitida.\n\n"
                    f"Seleccione las operaciones que el usuario puede realizar o "
                    f"cambie el tipo de acceso a 'Acceso completo'."
                )

    @api.constrains('operation_type_ids', 'warehouse_id')
    def _check_operations_belong_to_warehouse(self):
        """Validar que las operaciones seleccionadas pertenezcan al almacén."""
        for record in self:
            if record.operation_type_ids and record.warehouse_id:
                invalid_operations = record.operation_type_ids.filtered(
                    lambda op: op.warehouse_id != record.warehouse_id
                )
                if invalid_operations:
                    raise ValidationError(
                        f"Las siguientes operaciones NO pertenecen al almacén "
                        f"'{record.warehouse_id.name}':\n\n"
                        f"{', '.join(invalid_operations.mapped('name'))}\n\n"
                        f"Solo puede seleccionar operaciones del almacén configurado."
                    )

    # ========== COMPUTED FIELDS ==========

    @api.depends('user_id', 'warehouse_id')
    def _compute_name(self):
        """Generar nombre descriptivo automáticamente."""
        for record in self:
            if record.user_id and record.warehouse_id:
                record.name = f"{record.user_id.name} - {record.warehouse_id.name}"
            else:
                record.name = "Nuevo Acceso"

    @api.depends('rule_ids')
    def _compute_rule_count(self):
        """Contar reglas generadas."""
        for record in self:
            record.rule_count = len(record.rule_ids)

    # ========== CRUD OVERRIDES ==========

    @api.model_create_multi
    def create(self, vals_list):
        """Override create para generar record rules automáticamente."""
        records = super().create(vals_list)
        for record in records:
            try:
                record._generate_record_rules()
                _logger.info(
                    f"Acceso creado: Usuario '{record.user_id.name}' → "
                    f"Almacén '{record.warehouse_id.name}' ({record.access_type})"
                )
            except Exception as e:
                _logger.error(f"Error generando reglas para acceso {record.id}: {e}")
                raise ValidationError(
                    f"Error al generar reglas de seguridad: {str(e)}\n\n"
                    f"Contacte al administrador del sistema."
                )
        return records

    def write(self, vals):
        """Override write para actualizar record rules automáticamente."""
        result = super().write(vals)

        # Si se modifican campos críticos, regenerar reglas
        critical_fields = {'warehouse_id', 'access_type', 'operation_type_ids', 'active'}
        if any(field in vals for field in critical_fields):
            for record in self:
                try:
                    record._regenerate_record_rules()
                    _logger.info(
                        f"Acceso actualizado: Usuario '{record.user_id.name}' → "
                        f"Almacén '{record.warehouse_id.name}' ({record.access_type})"
                    )
                except Exception as e:
                    _logger.error(f"Error regenerando reglas para acceso {record.id}: {e}")
                    raise ValidationError(
                        f"Error al actualizar reglas de seguridad: {str(e)}\n\n"
                        f"Contacte al administrador del sistema."
                    )

        return result

    def unlink(self):
        """Override unlink para eliminar record rules asociadas."""
        for record in self:
            _logger.info(
                f"Eliminando acceso: Usuario '{record.user_id.name}' → "
                f"Almacén '{record.warehouse_id.name}'"
            )
            # Eliminar reglas asociadas (cascade automático)
        return super().unlink()

    # ========== RECORD RULES GENERATION ==========

    def _generate_record_rules(self):
        """
        Generar record rules de Odoo para aplicar restricciones de acceso.

        Crea reglas para los modelos:
        - stock.picking (operaciones de inventario)
        - stock.location (ubicaciones del almacén)
        - stock.warehouse (almacenes visibles)
        - stock.quant (existencias)
        """
        self.ensure_one()

        if not self.active:
            _logger.debug(f"Acceso {self.id} desactivado, no se generan reglas")
            return

        # Modelos para los cuales generar reglas
        models_to_restrict = [
            ('stock.picking', 'picking_type_id.warehouse_id'),
            ('stock.location', 'warehouse_id'),
            ('stock.warehouse', 'id'),
            ('stock.quant', 'location_id.warehouse_id'),
        ]

        AccessRule = self.env['amunet.warehouse.access.rule']

        for model_name, warehouse_field in models_to_restrict:
            domain = self._build_domain_for_model(model_name, warehouse_field)

            AccessRule.create({
                'access_id': self.id,
                'model_name': model_name,
                'domain_force': str(domain),
            })

    def _regenerate_record_rules(self):
        """Regenerar todas las reglas eliminando las existentes."""
        self.ensure_one()

        # Eliminar reglas existentes
        self.rule_ids.unlink()

        # Generar nuevas reglas
        self._generate_record_rules()

    def _build_domain_for_model(self, model_name, warehouse_field):
        """
        Construir dominio de Odoo para filtrar registros según acceso configurado.

        :param model_name: Nombre del modelo (ej: 'stock.picking')
        :param warehouse_field: Campo que relaciona con warehouse (ej: 'picking_type_id.warehouse_id')
        :return: Lista de tuplas (dominio Odoo)
        """
        self.ensure_one()

        # Dominio base: filtrar por almacén del usuario
        if model_name in ['stock.location', 'stock.quant']:
            domain = ['|', (warehouse_field, '=', self.warehouse_id.id), (warehouse_field, '=', False)]
        else:
            domain = [(warehouse_field, '=', self.warehouse_id.id)]

        # Si acceso restringido, agregar filtro por tipo de operación
        if self.access_type == 'restricted' and model_name == 'stock.picking':
            if self.operation_type_ids:
                domain.append(('picking_type_id', 'in', self.operation_type_ids.ids))
            else:
                # Sin operaciones = sin acceso (dominio imposible)
                domain = [('id', '=', False)]

        return domain

    # ========== HELPER METHODS ==========

    @api.model
    def _check_warehouse_access(self, user, warehouse, operation_type=None, raise_exception=False):
        """
        Validar si un usuario tiene acceso a un almacén y operación específica.

        :param user: res.users record
        :param warehouse: stock.warehouse record
        :param operation_type: stock.picking.type record (opcional)
        :param raise_exception: Si True, lanza ValidationError en caso de no tener acceso
        :return: Boolean (True si tiene acceso, False si no)
        """
        # Bypass para administradores
        if user.has_group('base.group_system'):
            return True

        # Buscar configuración de acceso
        access = self.sudo().search([
            ('user_id', '=', user.id),
            ('warehouse_id', '=', warehouse.id),
            ('active', '=', True),
        ], limit=1)

        if not access:
            if raise_exception:
                raise AccessError(
                    f"No tiene permiso para acceder al almacén '{warehouse.name}'.\n\n"
                    f"Contacte al administrador del sistema para solicitar acceso."
                )
            return False

        # Si tiene acceso completo, permitir
        if access.access_type == 'full':
            return True

        # Si tiene acceso restringido, validar operación específica
        if access.access_type == 'restricted':
            if not operation_type:
                # Sin operación especificada, denegar por seguridad
                if raise_exception:
                    raise AccessError(
                        f"Tiene acceso restringido al almacén '{warehouse.name}'. "
                        f"Especifique el tipo de operación."
                    )
                return False

            if operation_type not in access.operation_type_ids:
                if raise_exception:
                    raise AccessError(
                        f"No tiene permiso para realizar la operación '{operation_type.name}' "
                        f"en el almacén '{warehouse.name}'.\n\n"
                        f"Operaciones permitidas: {', '.join(access.operation_type_ids.mapped('name'))}"
                    )
                return False

        return True

    def action_view_rules(self):
        """Acción para ver reglas generadas."""
        self.ensure_one()
        return {
            'name': f'Reglas: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.warehouse.access.rule',
            'view_mode': 'list,form',
            'domain': [('access_id', '=', self.id)],
            'context': {'default_access_id': self.id},
        }

    # ========== INIT HOOK ==========

    @api.model
    def _init_visibility_rules(self):
        """
        Inicializar reglas de visibilidad para que usuarios siempre vean sus propios registros.
        
        Este método se ejecuta después de la instalación/actualización del módulo
        para crear las reglas de acceso globales de forma segura.
        """
        IrRule = self.env['ir.rule']
        IrModel = self.env['ir.model']
        IrModelData = self.env['ir.model.data']
        
        # Verificar que los modelos existan antes de crear reglas
        model_access_rule = IrModel.search([('model', '=', 'amunet.warehouse.access.rule')], limit=1)
        model_access = IrModel.search([('model', '=', 'amunet.warehouse.access')], limit=1)
        
        if not model_access_rule or not model_access:
            _logger.warning("Modelos no encontrados, saltando creación de reglas de visibilidad")
            return
        
        # Regla 1: amunet.warehouse.access.rule
        xml_id_rule = 'amunet_warehouse_access.rule_warehouse_access_rule_own_records'
        existing_rule_id = IrModelData._xmlid_to_res_id(xml_id_rule, raise_if_not_found=False)
        
        if not existing_rule_id:
            try:
                rule = IrRule.sudo().create({
                    'name': 'Reglas de Acceso: Ver Propios Registros',
                    'model_id': model_access_rule.id,
                    'domain_force': "[('user_id', '=', user.id)]",
                    'global': True,
                    'active': True,
                })
                IrModelData.sudo().create({
                    'name': 'rule_warehouse_access_rule_own_records',
                    'module': 'amunet_warehouse_access',
                    'model': 'ir.rule',
                    'res_id': rule.id,
                })
                _logger.info("Regla de visibilidad para amunet.warehouse.access.rule creada")
            except Exception as e:
                _logger.warning(f"Error creando regla de visibilidad para access.rule: {e}")
        
        # Regla 2: amunet.warehouse.access
        xml_id_access = 'amunet_warehouse_access.rule_warehouse_access_own_records'
        existing_access_id = IrModelData._xmlid_to_res_id(xml_id_access, raise_if_not_found=False)
        
        if not existing_access_id:
            try:
                rule = IrRule.sudo().create({
                    'name': 'Accesos a almacenes: Ver propios registros',
                    'model_id': model_access.id,
                    'domain_force': "[('user_id', '=', user.id)]",
                    'global': True,
                    'active': True,
                })
                IrModelData.sudo().create({
                    'name': 'rule_warehouse_access_own_records',
                    'module': 'amunet_warehouse_access',
                    'model': 'ir.rule',
                    'res_id': rule.id,
                })
                _logger.info("Regla de visibilidad para amunet.warehouse.access creada")
            except Exception as e:
                _logger.warning(f"Error creando regla de visibilidad para access: {e}")

    # ========== UNINSTALL HOOK ==========

    @api.model
    def _uninstall_hook(self):
        """
        Hook de desinstalación del módulo.
        
        Se ejecuta automáticamente cuando se desinstala el módulo.
        Limpia todos los registros creados dinámicamente antes de que
        Odoo intente eliminarlos, evitando errores de restricciones de clave foránea.
        """
        # Llamar al método de limpieza del modelo de reglas
        self.env['amunet.warehouse.access.rule']._uninstall_cleanup()
