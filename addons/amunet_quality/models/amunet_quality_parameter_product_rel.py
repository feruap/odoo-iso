# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AmunetQualityParameterProductRel(models.Model):
    """
    Relación Producto-Parámetro de Calidad.

    Tabla intermedia que vincula productos con parámetros de calidad,
    permitiendo configurar especificaciones específicas por producto.

    Epic-031: Sistema de Parámetros de Calidad Jerárquicos
    T-031-4: Crear relación producto-parámetro-especificación
    """
    _name = 'amunet.quality.parameter.product.rel'
    _description = 'Relación Producto-Parámetro de Calidad'
    _order = 'sequence, id'
    _rec_name = 'display_name'

    # ========== Relaciones Principales ==========

    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Producto',
        required=True,
        ondelete='cascade',
        index=True
    )

    parameter_id = fields.Many2one(
        'amunet.quality.check.parameter',
        string='Parámetro',
        required=True,
        ondelete='restrict',
        index=True
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden del parámetro en el producto'
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Indica si esta configuración de parámetro está activa.'
    )

    # ========== Configuración de Especificaciones ==========

    specification_config_ids = fields.One2many(
        'amunet.quality.parameter.specification.config',
        'product_parameter_rel_id',
        string='Configuración de especificaciones',
        help='Configuración específica de cada especificación para este producto'
    )

    # ========== Campos Relacionados (para mostrar en vistas) ==========

    parameter_code = fields.Char(
        string='Código',
        related='parameter_id.code',
        store=True
    )

    parameter_name = fields.Char(
        string='Determinación',
        related='parameter_id.name',
        store=True
    )

    specification_total = fields.Integer(
        string='Esp. Totales',
        related='parameter_id.specification_count'
    )

    # ========== Campos Computados ==========

    active_spec_count = fields.Integer(
        string='Esp. Activas',
        compute='_compute_active_spec_count',
        store=True
    )

    spec_summary = fields.Char(
        string='Resumen',
        compute='_compute_spec_summary',
        store=True
    )

    display_name = fields.Char(
        string='Nombre',
        compute='_compute_display_name',
        store=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        related='product_tmpl_id.company_id',
        store=True
    )

    @api.depends('specification_config_ids', 'specification_config_ids.active')
    def _compute_active_spec_count(self):
        """Cuenta las especificaciones activas para este producto"""
        for record in self:
            record.active_spec_count = len(
                record.specification_config_ids.filtered(lambda c: c.active)
            )

    @api.depends('specification_config_ids', 'specification_config_ids.nominal_value', 
                 'specification_config_ids.max_value_manual', 'specification_config_ids.acceptance_criteria')
    def _compute_spec_summary(self):
        """Genera resumen de especificaciones con valores: 'Ancho: 18, Largo: 48'"""
        # Prefetch de configuraciones para todos los registros procesados
        self.specification_config_ids.mapped('specification_id') # Trigger prefetch
        
        for record in self:
            # Filtrar solo las que tienen algún valor real configurado
            configs = record.specification_config_ids.filtered(
                lambda s: s.nominal_value > 0 or s.max_value_manual > 0 or s.min_value_manual > 0 or s.acceptance_criteria
            )
            
            if not configs:
                record.spec_summary = "Sin valores"
                continue

            summary_parts = []
            # Tomar las primeras 3 para no saturar la vista de lista
            for config in configs[:3]:
                name = config.specification_id.name or "?"
                if config.nominal_value > 0:
                    val = f"{config.nominal_value}"
                elif config.max_value_manual > 0:
                    val = f"<{config.max_value_manual}"
                elif config.min_value_manual > 0:
                    val = f">{config.min_value_manual}"
                elif config.acceptance_criteria:
                    val = "OK"
                else:
                    val = "?"
                summary_parts.append(f"{name}: {val}")
            
            suffix = "..." if len(configs) > 3 else ""
            record.spec_summary = ", ".join(summary_parts) + suffix

    @api.depends('parameter_code', 'parameter_name')
    def _compute_display_name(self):
        """Genera nombre para mostrar: '[CÓDIGO] Determinación'"""
        for record in self:
            parts = []
            if record.parameter_code:
                parts.append(f'[{record.parameter_code}]')
            if record.parameter_name:
                parts.append(record.parameter_name)
            record.display_name = ' '.join(parts) if parts else 'Parámetro'

    # ========== Métodos de Acción ==========

    def action_configure_specifications(self):
        """Abre wizard/modal para configurar especificaciones del parámetro para este producto"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Configurar: {self.display_name}',
            'res_model': 'amunet.quality.parameter.product.rel',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # ========== Onchange ==========

    @api.onchange('parameter_id')
    def _onchange_parameter_id(self):
        """Al seleccionar parámetro, genera configuraciones para sus especificaciones"""
        if self.parameter_id:
            # Esto se ejecutará al guardar, no en onchange
            # Ver método create() y write()
            pass

    # ========== Métodos CRUD ==========

    @api.model_create_multi
    def create(self, vals_list):
        """Al crear relación, genera configuraciones para las especificaciones del parámetro"""
        records = super().create(vals_list)
        for record in records:
            record._generate_specification_configs()
        return records

    def _generate_specification_configs(self):
        """
        Genera configuraciones de especificación para este producto-parámetro.
        Copia los valores por defecto desde la especificación base.
        """
        self.ensure_one()

        # Si ya tiene configuraciones, no regenerar
        if self.specification_config_ids:
            return

        if not self.parameter_id or not self.parameter_id.specification_line_ids:
            return

        SpecConfig = self.env['amunet.quality.parameter.specification.config']
        
        config_vals = []
        for spec in self.parameter_id.specification_line_ids:
            # Copiar TODOS los valores de la especificación como defaults
            vals = {
                'product_parameter_rel_id': self.id,
                'specification_id': spec.id,
                'active': True,
                'sequence': spec.sequence,
                # Criterio de aceptación
                'acceptance_criteria': spec.acceptance_criteria,
                'uom_id': spec.uom_id.id if spec.uom_id else False,
                # Binary selection
                'binary_prefix': spec.binary_prefix,
                'binary_suffix': spec.binary_suffix,
                'binary_expected_option': spec.binary_expected_option,
                # Checkbox combined
                'checkbox_label_1': spec.checkbox_label_1,
                'checkbox_label_2': spec.checkbox_label_2,
                'checkbox_require_both': spec.checkbox_require_both,
                # Text pattern
                'text_pattern_expected': spec.text_pattern_expected,
                'text_pattern_regex': spec.text_pattern_regex,
                'text_phrase_mapping': spec.text_phrase_mapping,
                # Expected vs Obtained
                'expected_options': spec.expected_options,
                'obtained_options': spec.obtained_options,
                # Binary with notes
                'binary_notes_option_pass': spec.binary_notes_option_pass,
                'binary_notes_option_fail': spec.binary_notes_option_fail,
                'binary_notes_required': spec.binary_notes_required,
                # Ternary
                'ternary_option_yes': spec.ternary_option_yes,
                'ternary_option_no': spec.ternary_option_no,
                'ternary_option_na': spec.ternary_option_na,
                # Numeric range (Added in personalization fix)
                'nominal_value': spec.nominal_value,
                'tolerance': spec.tolerance,
                'min_value_manual': spec.min_value_manual,
                'max_value_manual': spec.max_value_manual,
                'use_manual_range': spec.use_manual_range,
                'min_value': spec.min_value,
                'max_value': spec.max_value,
            }
            config_vals.append(vals)

        if config_vals:
            config_records = SpecConfig.create(config_vals)
            # Copiar opciones condicionales después de crear los registros
            for config_record, spec in zip(config_records, self.parameter_id.specification_line_ids):
                if spec.conditional_option_ids:
                    config_record.active_conditional_option_ids = spec.conditional_option_ids

    def action_regenerate_configs(self):
        """Regenera las configuraciones de especificación (elimina existentes)"""
        self.ensure_one()
        self.specification_config_ids.unlink()
        self._generate_specification_configs()
        return True

    # ========== Métodos de Utilidad ==========

    def get_active_specifications(self):
        """Retorna las especificaciones activas para este producto-parámetro"""
        self.ensure_one()
        return self.specification_config_ids.filtered(lambda c: c.active)

    def get_test_line_values(self):
        """
        Prepara los valores para crear una línea de test en el QC.
        
        Returns:
            dict: Valores para amunet.quality.test.line
        """
        self.ensure_one()
        return {
            'parameter_id': self.parameter_id.id,
            'name': self.parameter_id.name,
            'sequence': self.sequence,
            # Los detalles se generan desde las especificaciones activas
        }

