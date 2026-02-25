# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
import ast

_logger = logging.getLogger(__name__)


class AmunetWarehouseAccessRule(models.Model):
    """
    Metadatos de Record Rules generadas automáticamente.

    Este modelo almacena información sobre las reglas de Odoo (ir.rule) generadas
    para cada configuración de acceso. Permite trazabilidad y gestión de reglas dinámicas.

    Epic-033: Control de Acceso Dinámico por Almacén
    """
    _name = 'amunet.warehouse.access.rule'
    _description = 'Reglas de Acceso a Almacenes'
    _order = 'access_id, model_name'

    # ========== FIELDS ==========

    name = fields.Char(
        string='Nombre',
        compute='_compute_name',
        store=True,
        index=True
    )

    access_id = fields.Many2one(
        comodel_name='amunet.warehouse.access',
        string='Configuración de control de acceso',
        required=True,
        index=True,
        ondelete='cascade'
    )

    rule_id = fields.Many2one(
        comodel_name='ir.rule',
        string='Regla de Odoo',
        readonly=True,
        ondelete='cascade',
        help="Record rule de Odoo generada automáticamente."
    )

    model_name = fields.Char(
        string='Modelo',
        required=True,
        index=True,
        help="Nombre técnico del modelo (ej: 'stock.picking')"
    )

    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Modelo (Registro)',
        compute='_compute_model_id',
        store=True,
        help="Registro ir.model correspondiente al modelo."
    )

    domain_force = fields.Text(
        string='Dominio',
        required=True,
        help="Dominio de Odoo aplicado para filtrar registros."
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
        help="Si está desactivado, la regla no se aplica."
    )

    # Campos relacionados para información
    user_id = fields.Many2one(
        related='access_id.user_id',
        string='Usuario',
        store=True,
        index=True,
        readonly=True
    )

    warehouse_id = fields.Many2one(
        related='access_id.warehouse_id',
        string='Almacén',
        store=True,
        index=True,
        readonly=True
    )

    access_type = fields.Selection(
        related='access_id.access_type',
        string='Tipo de control de acceso',
        readonly=True
    )

    # ========== COMPUTED FIELDS ==========

    @api.depends('access_id', 'model_name')
    def _compute_name(self):
        """Generar nombre descriptivo automáticamente."""
        for record in self:
            if record.access_id and record.model_name:
                model_display = record.model_name.replace('.', ' ').title()
                record.name = (
                    f"Acceso {record.access_id.user_id.name} - "
                    f"{record.access_id.warehouse_id.name} - {model_display}"
                )
            else:
                record.name = "Nueva Regla"

    @api.depends('model_name')
    def _compute_model_id(self):
        """Obtener ir.model desde el nombre del modelo."""
        IrModel = self.env['ir.model']
        for record in self:
            if record.model_name:
                model = IrModel.search([('model', '=', record.model_name)], limit=1)
                record.model_id = model.id if model else False
            else:
                record.model_id = False

    # ========== CRUD OVERRIDES ==========

    @api.model_create_multi
    def create(self, vals_list):
        """Override create para generar ir.rule automáticamente."""
        records = super().create(vals_list)

        for record in records:
            try:
                record._create_odoo_rule()
                _logger.info(
                    f"Regla generada: {record.model_name} para usuario "
                    f"'{record.user_id.name}' en almacén '{record.warehouse_id.name}'"
                )
            except Exception as e:
                _logger.error(f"Error creando ir.rule para {record.id}: {e}")
                raise ValidationError(
                    f"Error al crear regla de seguridad de Odoo: {str(e)}\n\n"
                    f"Verifique los permisos del sistema."
                )

        return records

    def write(self, vals):
        """Override write para actualizar ir.rule si cambia dominio o estado."""
        result = super().write(vals)

        # Si cambia dominio o estado activo, actualizar ir.rule
        if 'domain_force' in vals or 'active' in vals:
            for record in self:
                try:
                    record._update_odoo_rule()
                except Exception as e:
                    _logger.error(f"Error actualizando ir.rule para {record.id}: {e}")
                    raise ValidationError(
                        f"Error al actualizar regla de seguridad: {str(e)}"
                    )

        return result

    def unlink(self):
        """Override unlink para eliminar ir.rule asociada."""
        for record in self:
            if record.rule_id:
                try:
                    _logger.info(
                        f"Eliminando regla de Odoo: {record.rule_id.name} (ID: {record.rule_id.id})"
                    )
                    record.rule_id.unlink()
                except Exception as e:
                    _logger.warning(f"No se pudo eliminar ir.rule {record.rule_id.id}: {e}")

        return super().unlink()

    # ========== IR.RULE MANAGEMENT ==========

    def _create_odoo_rule(self):
        """Crear registro ir.rule de Odoo."""
        self.ensure_one()

        if self.rule_id:
            _logger.warning(f"Regla {self.id} ya tiene ir.rule asociada (ID: {self.rule_id.id})")
            return

        if not self.model_id:
            raise ValidationError(
                f"No se encontró el modelo '{self.model_name}' en el sistema.\n"
                f"Verifique que el módulo correspondiente esté instalado."
            )

        # Crear grupo único para este usuario si no existe
        group = self._get_or_create_user_group()

        # Validar y parsear dominio
        domain = self._validate_and_parse_domain()

        # Crear ir.rule
        rule_vals = {
            'name': self.name,
            'model_id': self.model_id.id,
            'domain_force': str(domain),
            'groups': [(6, 0, [group.id])],
            'active': self.active,
            'perm_read': True,
            'perm_write': True,
            'perm_create': True,
            'perm_unlink': True,
        }

        rule = self.env['ir.rule'].sudo().create(rule_vals)
        self.rule_id = rule.id

        _logger.info(f"ir.rule creada: {rule.name} (ID: {rule.id})")

    def _update_odoo_rule(self):
        """Actualizar ir.rule existente."""
        self.ensure_one()

        if not self.rule_id:
            _logger.warning(f"Regla {self.id} no tiene ir.rule asociada, creando nueva")
            self._create_odoo_rule()
            return

        domain = self._validate_and_parse_domain()

        self.rule_id.sudo().write({
            'domain_force': str(domain),
            'active': self.active,
        })

        _logger.info(f"ir.rule actualizada: {self.rule_id.name} (ID: {self.rule_id.id})")

    def _get_or_create_user_group(self):
        """
        Obtener o crear grupo único para el usuario.

        Cada usuario con accesos personalizados obtiene un grupo único
        para aplicar sus Record Rules específicas.
        """
        self.ensure_one()

        group_xml_id = f'amunet_warehouse_access.group_warehouse_access_user_{self.user_id.id}'
        group_name = f'Acceso a almacenes: {self.user_id.name}'

        # Buscar grupo existente
        IrModelData = self.env['ir.model.data']
        group = IrModelData._xmlid_to_res_id(group_xml_id, raise_if_not_found=False)

        if group:
            return self.env['res.groups'].browse(group)

        # Crear nuevo grupo
        # En Odoo 19, res.groups no tiene category_id directamente
        # Se usa privilege_id si se necesita categorización, pero para grupos dinámicos
        # es mejor crearlos sin privilegio específico
        group_vals = {
            'name': group_name,
        }

        # Crear el grupo primero
        group = self.env['res.groups'].sudo().create(group_vals)
        
        # Asignar el usuario al grupo después de crearlo
        # En Odoo 19, el campo correcto es user_ids (Many2many)
        group.sudo().user_ids = [(4, self.user_id.id)]

        # Registrar XML ID para reutilización
        IrModelData.sudo().create({
            'name': f'group_warehouse_access_user_{self.user_id.id}',
            'module': 'amunet_warehouse_access',
            'model': 'res.groups',
            'res_id': group.id,
        })

        _logger.info(f"Grupo creado: {group_name} (ID: {group.id})")

        return group

    def _validate_and_parse_domain(self):
        """
        Validar y parsear el dominio almacenado como texto.

        :return: Lista de tuplas (dominio Odoo válido)
        """
        self.ensure_one()

        if not self.domain_force:
            raise ValidationError(
                f"La regla '{self.name}' no tiene dominio definido.\n"
                f"No se puede crear una regla vacía."
            )

        try:
            # Convertir string a lista de Python
            domain = ast.literal_eval(self.domain_force)

            # Validar que sea lista
            if not isinstance(domain, list):
                raise ValueError("El dominio debe ser una lista de tuplas")

            # Validar estructura básica
            for clause in domain:
                if isinstance(clause, tuple) and len(clause) >= 2:
                    continue
                elif isinstance(clause, str) and clause in ['&', '|', '!']:
                    continue
                else:
                    raise ValueError(f"Cláusula inválida en dominio: {clause}")

            return domain

        except Exception as e:
            raise ValidationError(
                f"Dominio inválido para la regla '{self.name}':\n\n"
                f"{self.domain_force}\n\n"
                f"Error: {str(e)}"
            )

    # ========== ACTIONS ==========

    def action_view_odoo_rule(self):
        """Acción para ver la ir.rule de Odoo."""
        self.ensure_one()

        if not self.rule_id:
            raise ValidationError(
                f"Esta regla no tiene ir.rule asociada.\n"
                f"Verifique la configuración del sistema."
            )

        return {
            'name': f'Regla de Odoo: {self.rule_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.rule',
            'view_mode': 'form',
            'res_id': self.rule_id.id,
            'target': 'current',
        }

    # ========== UNINSTALL HOOK ==========

    @api.model
    def _uninstall_cleanup(self):
        """
        Limpiar registros creados dinámicamente antes de desinstalar el módulo.
        
        Este método debe llamarse desde el hook de desinstalación del módulo.
        Elimina en orden:
        1. Reglas ir.rule creadas dinámicamente
        2. Grupos res.groups creados dinámicamente
        3. Registros de amunet.warehouse.access.rule
        4. Registros de amunet.warehouse.access
        
        El orden es crítico debido a las dependencias de clave foránea.
        """
        _logger.info("Iniciando limpieza de registros dinámicos de amunet_warehouse_access...")

        # 1. Eliminar todas las reglas ir.rule asociadas
        # Buscar todas las reglas que fueron creadas por este módulo
        AccessRule = self.env['amunet.warehouse.access.rule']
        all_rules = AccessRule.search([])
        
        rule_ids_to_delete = []
        for rule in all_rules:
            if rule.rule_id:
                rule_ids_to_delete.append(rule.rule_id.id)
        
        if rule_ids_to_delete:
            _logger.info(f"Eliminando {len(rule_ids_to_delete)} reglas ir.rule...")
            try:
                self.env['ir.rule'].sudo().browse(rule_ids_to_delete).unlink()
                _logger.info(f"✓ {len(rule_ids_to_delete)} reglas ir.rule eliminadas")
            except Exception as e:
                _logger.warning(f"Error eliminando reglas ir.rule: {e}")

        # 2. Eliminar todos los grupos res.groups creados dinámicamente
        # Buscar grupos con XML ID que empiecen con 'amunet_warehouse_access.group_warehouse_access_user_'
        IrModelData = self.env['ir.model.data']
        group_xml_ids = IrModelData.search([
            ('module', '=', 'amunet_warehouse_access'),
            ('model', '=', 'res.groups'),
            ('name', 'like', 'group_warehouse_access_user_%')
        ])
        
        group_ids_to_delete = []
        for xml_id in group_xml_ids:
            if xml_id.res_id:
                group_ids_to_delete.append(xml_id.res_id)
        
        if group_ids_to_delete:
            _logger.info(f"Eliminando {len(group_ids_to_delete)} grupos res.groups...")
            try:
                # Primero desasociar usuarios de los grupos
                groups = self.env['res.groups'].sudo().browse(group_ids_to_delete)
                for group in groups:
                    group.user_ids = [(5, 0, 0)]  # Desasociar todos los usuarios
                
                # Luego eliminar los grupos
                groups.unlink()
                _logger.info(f"✓ {len(group_ids_to_delete)} grupos res.groups eliminados")
            except Exception as e:
                _logger.warning(f"Error eliminando grupos res.groups: {e}")

        # 3. Eliminar registros de amunet.warehouse.access.rule
        if all_rules:
            _logger.info(f"Eliminando {len(all_rules)} registros de amunet.warehouse.access.rule...")
            try:
                all_rules.sudo().unlink()
                _logger.info(f"✓ {len(all_rules)} registros de amunet.warehouse.access.rule eliminados")
            except Exception as e:
                _logger.warning(f"Error eliminando registros de amunet.warehouse.access.rule: {e}")

        # 4. Eliminar registros de amunet.warehouse.access
        Access = self.env['amunet.warehouse.access']
        all_accesses = Access.search([])
        if all_accesses:
            _logger.info(f"Eliminando {len(all_accesses)} registros de amunet.warehouse.access...")
            try:
                all_accesses.sudo().unlink()
                _logger.info(f"✓ {len(all_accesses)} registros de amunet.warehouse.access eliminados")
            except Exception as e:
                _logger.warning(f"Error eliminando registros de amunet.warehouse.access: {e}")

        # 5. Limpiar XML IDs huérfanos
        orphaned_xml_ids = IrModelData.search([
            ('module', '=', 'amunet_warehouse_access'),
            ('model', 'in', ['res.groups', 'ir.rule'])
        ])
        if orphaned_xml_ids:
            _logger.info(f"Eliminando {len(orphaned_xml_ids)} XML IDs huérfanos...")
            try:
                orphaned_xml_ids.sudo().unlink()
                _logger.info(f"✓ {len(orphaned_xml_ids)} XML IDs eliminados")
            except Exception as e:
                _logger.warning(f"Error eliminando XML IDs: {e}")

        _logger.info("Limpieza de registros dinámicos completada.")
