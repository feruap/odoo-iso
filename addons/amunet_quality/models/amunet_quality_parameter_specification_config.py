# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AmunetQualityParameterSpecificationConfig(models.Model):
    """
    Configuración de Especificación por Producto.

    Permite configurar valores específicos (nominal, tolerancia, min/max)
    para cada especificación de un parámetro en un producto específico.

    Ejemplo: MAVI-11 en MPBOL01 tiene Ancho=60±1mm, Largo=120±1mm
             MAVI-11 en MPBOL05 tiene Ancho1=55±1mm, Ancho2=50±1mm, Largo=120±1mm

    Epic-031: Sistema de Parámetros de Calidad Jerárquicos
    T-031-4: Crear relación producto-parámetro-especificación
    """
    _name = 'amunet.quality.parameter.specification.config'
    _description = 'Configuración de especificación por producto'
    _order = 'sequence, id'

    # ========== Relaciones ==========

    product_parameter_rel_id = fields.Many2one(
        'amunet.quality.parameter.product.rel',
        string='Relación Producto-Parámetro',
        required=True,
        ondelete='cascade',
        index=True
    )

    specification_id = fields.Many2one(
        'amunet.quality.check.parameter.specification',
        string='Especificación',
        required=True,
        ondelete='cascade',
        index=True
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )

    # ========== Control de Activación ==========

    active = fields.Boolean(
        string='Activa',
        default=True,
        help='Si esta especificación aplica para este producto'
    )

    # ========== Campos Relacionados (solo lectura) ==========

    specification_name = fields.Char(
        string='Nombre',
        related='specification_id.name',
        store=True
    )

    evaluation_type = fields.Selection([
        ('binary_selection', 'Selección binaria (Sin/Con)'),
        ('numeric_range', 'Rango numérico'),
        ('checkbox_combined', 'Checkboxes combinados'),
        ('conditional_numeric_range', 'Rango numérico condicional'),
        ('text_pattern', 'Texto con patrón'),
        ('expected_vs_obtained', 'Comparación esperado vs obtenido'),
        ('binary_with_notes', 'Binario con notas'),
        ('ternary_with_na', 'Ternario con N/A'),
        ('decision_matrix', 'Matriz de decisión (Multi-paso)'),
        ('mavi_07', 'MAVI-07: Visualización de Líneas Resultado'),
        ('multi_condition_numeric', 'Multi-Condición Numérica (VAMA-096)'),
        ('vama_044', 'VAMA-044: Funcionalidad de Tubo (4 condiciones)'),
        ('vama_112', 'VAMA-112: Multi-Checkbox Centrífuga'),
        ('vama_078', 'VAMA-078: Multi-Visual Liofilizado'),
        ('vama_multi_check', 'VAMA: Multi-Check Genérico (1-6 puntos)'),
        ('mga_0981', 'MGA-0981: Variación de Volumen (± 0.5 ml)'),
        ('vama_105', 'VAMA-105: Volumen Nominal vs Medido'),
        ('vama_034', 'VAMA-034: Tipo Muestra vs Resultado'),
        ('vama_006', 'VAMA-006: Escala de Color 0-14'),
        ('vama_067', 'VAMA-067: Selección 2 Pasos (Partículas/Color)'),
        ('mavi_15_ternary', 'MAVI-15: Selección Ternaria'),
        ('mavi_11_height', 'MAVI-11: Altura (6/8 cm ± 0.5)'),
        ('mavi_07_ternary', 'MAVI-07: Ternario (Hojas Maestras)'),
    ], string='Tipo Evaluación',
        related='specification_id.evaluation_type',
        store=True
    )

    acceptance_criteria = fields.Char(
        string='Criterio de aceptación',
        help='Descripción del criterio para este producto'
    )

    uom_id = fields.Many2one(
        'uom.uom',
        string='Unidad de medida',
        help='Unidad de medida para valores numéricos'
    )

    product_tmpl_id = fields.Many2one(
        string='Producto',
        related='product_parameter_rel_id.product_tmpl_id',
        store=True
    )

    parameter_id = fields.Many2one(
        string='Parámetro',
        related='product_parameter_rel_id.parameter_id',
        store=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        related='product_parameter_rel_id.company_id',
        store=True
    )

    # ========== Configuración Binary Selection ==========

    binary_prefix = fields.Char(
        string='Prefijo',
        help='Prefijo para opciones binarias (ej: Sin/Con, Sellado/No sellado)'
    )

    binary_suffix = fields.Char(
        string='Sufijo',
        help='Sufijo para opciones binarias (ej: polvo, manchas)'
    )

    binary_expected_option = fields.Selection([
        ('with_prefix', 'Con prefijo (ej: Sin polvo)'),
        ('without_prefix', 'Sin prefijo (ej: Con polvo)'),
    ], string='Opción esperada', default='with_prefix',
        help='Qué opción se considera que CUMPLE')

    binary_option_pass = fields.Char(
        string='Opción que cumple',
        compute='_compute_binary_options',
        store=True
    )

    binary_option_fail = fields.Char(
        string='Opción que no cumple',
        compute='_compute_binary_options',
        store=True
    )

    # ========== Configuración Numeric Range ==========

    nominal_value = fields.Float(
        string='Valor nominal',
        digits='Product Unit of Measure',
        help='Valor nominal/objetivo (ej: 60 mm)'
    )

    tolerance = fields.Float(
        string='Tolerancia (±)',
        digits='Product Unit of Measure',
        help='Tolerancia aplicada al valor nominal (ej: ±1 mm)'
    )

    min_value = fields.Float(
        string='Mínimo',
        digits='Product Unit of Measure',
        compute='_compute_min_max',
        store=True,
        help='Valor mínimo aceptable (nominal - tolerancia)'
    )

    max_value = fields.Float(
        string='Máximo',
        digits='Product Unit of Measure',
        compute='_compute_min_max',
        store=True,
        help='Valor máximo aceptable (nominal + tolerancia)'
    )

    min_value_manual = fields.Float(
        string='Mínimo manual',
        digits='Product Unit of Measure',
        help='Valor mínimo ingresado manualmente'
    )

    max_value_manual = fields.Float(
        string='Máximo manual',
        digits='Product Unit of Measure',
        help='Valor máximo ingresado manualmente'
    )

    use_manual_range = fields.Boolean(
        string='Usar rango manual',
        default=False,
        help='Usar valores min/max manuales en lugar del cálculo automático'
    )

    # ========== Configuración Checkbox Combined ==========

    checkbox_label_1 = fields.Char(
        string='Checkbox 1',
        help='Etiqueta del primer checkbox (ej: Sellado adecuado)'
    )

    checkbox_label_2 = fields.Char(
        string='Checkbox 2',
        help='Etiqueta del segundo checkbox (ej: Sin defectos visibles)'
    )

    checkbox_require_both = fields.Boolean(
        string='Requiere ambos',
        default=True,
        help='Si está activo, CUMPLE solo si ambos checkboxes están marcados'
    )

    # ========== Configuración Text Pattern ==========

    text_pattern_expected = fields.Char(
        string='Patrón esperado',
        help='Patrón esperado que debe coincidir (ej: AAAAA)'
    )

    text_pattern_regex = fields.Char(
        string='Expresión regular',
        help='Regex para validar formato (ej: ^[AB]{5}$)'
    )

    text_pattern_length = fields.Integer(
        string='Longitud del patrón',
        compute='_compute_text_pattern_length',
        store=True
    )

    text_phrase_mapping = fields.Text(
        string='Mapeo de frases (JSON)',
        help='JSON con mapeo de posiciones a frases descriptivas'
    )

    # ========== Configuración Expected vs Obtained ==========

    expected_options = fields.Char(
        string='Opciones esperadas',
        help='Opciones separadas por coma (ej: Positivo,Negativo)'
    )

    obtained_options = fields.Char(
        string='Opciones obtenidas',
        help='Opciones separadas por coma (ej: Positivo,Negativo)'
    )

    # ========== Configuración Binary with Notes ==========

    binary_notes_option_pass = fields.Char(
        string='Opción que cumple (con notas)',
        help='Texto de la opción que cumple'
    )

    binary_notes_option_fail = fields.Char(
        string='Opción que no cumple (con notas)',
        help='Texto de la opción que no cumple'
    )

    binary_notes_required = fields.Boolean(
        string='Notas requeridas si no cumple',
        default=True,
        help='Si está activo, las notas son obligatorias cuando no cumple'
    )

    # ========== Configuración Ternary with N/A ==========

    ternary_option_yes = fields.Char(
        string='Opción sí',
        default='Sí',
        help='Texto para la opción que cumple'
    )

    ternary_option_no = fields.Char(
        string='Opción no',
        default='No',
        help='Texto para la opción que no cumple'
    )

    ternary_option_na = fields.Char(
        string='Opción N/A',
        default='N/A',
        help='Texto para la opción no aplicable'
    )

    # ========== Configuración Conditional Numeric Range ==========

    active_conditional_option_ids = fields.Many2many(
        'amunet.quality.parameter.conditional.option',
        'spec_config_conditional_option_rel',
        'config_id',
        'option_id',
        string='Opciones Activas',
        help='Opciones condicionales activas para este producto'
    )

    # ========== Campos Computados ==========

    range_display = fields.Char(
        string='Rango',
        compute='_compute_range_display',
        store=True
    )

    config_summary = fields.Char(
        string='Resumen',
        compute='_compute_config_summary',
        store=True
    )

    @api.depends('binary_prefix', 'binary_suffix', 'binary_expected_option')
    def _compute_binary_options(self):
        """
        Genera las opciones de selección binaria.

        Lógica de construcción:
        1. Si ambos vacíos → campos vacíos
        2. Si solo prefix (suffix vacío) → usar prefix directamente (formato "opción1/opción2")
        3. Si solo suffix (prefix vacío) → campos vacíos
        4. Si ambos configurados → concatenar "prefix suffix"

        Ejemplos:
        - prefix="", suffix="" → "" / ""
        - prefix="Letra legible/Letra ilegible", suffix="" → "Letra legible" / "Letra ilegible"
        - prefix="", suffix="polvo" → "" / ""
        - prefix="Sin/Con", suffix="polvo" → "Sin polvo" / "Con polvo"
        - prefix="Sellado", suffix="adecuado" → "Sellado adecuado" / "No sellado adecuado"
        """
        for record in self:
            # Caso 1: Ambos vacíos → dejar campos vacíos
            if not record.binary_prefix and not record.binary_suffix:
                record.binary_option_pass = ''
                record.binary_option_fail = ''
                continue

            # Caso 2: Solo prefix (suffix vacío) → usar prefix directamente
            if record.binary_prefix and not record.binary_suffix:
                # Support '|' as separator to allow '/' in text (e.g. units)
                separator = '|' if '|' in record.binary_prefix else '/'
                prefix_parts = record.binary_prefix.split(separator)
                if len(prefix_parts) >= 2:
                    # Formato "Letra legible/Letra ilegible" → usar directamente
                    option_with = prefix_parts[0].strip()
                    option_without = prefix_parts[1].strip()
                else:
                    # Sin "/" en prefix, usar como única opción
                    option_with = record.binary_prefix.strip()
                    option_without = f"No {record.binary_prefix.lower()}"

                if record.binary_expected_option == 'with_prefix':
                    record.binary_option_pass = option_with
                    record.binary_option_fail = option_without
                else:
                    record.binary_option_pass = option_without
                    record.binary_option_fail = option_with
                continue

            # Caso 3: Solo suffix (prefix vacío) → dejar campos vacíos
            if not record.binary_prefix and record.binary_suffix:
                record.binary_option_pass = ''
                record.binary_option_fail = ''
                continue

            # Caso 4: Ambos configurados → concatenar "prefix suffix"
            # Support '|' as separator to allow '/' in text (e.g. units)
            separator = '|' if '|' in record.binary_prefix else '/'
            prefix_parts = record.binary_prefix.split(separator)
            if len(prefix_parts) >= 2:
                # Formato "Sin/Con" + "polvo" → "Sin polvo" / "Con polvo"
                option_with = f"{prefix_parts[0].strip()} {record.binary_suffix}"
                option_without = f"{prefix_parts[1].strip()} {record.binary_suffix}"
            else:
                # Formato simple "Sellado" + "adecuado" → "Sellado adecuado" / "No sellado adecuado"
                option_with = f"{record.binary_prefix} {record.binary_suffix}"
                option_without = f"No {record.binary_prefix.lower()} {record.binary_suffix}"

            if record.binary_expected_option == 'with_prefix':
                record.binary_option_pass = option_with
                record.binary_option_fail = option_without
            else:
                record.binary_option_pass = option_without
                record.binary_option_fail = option_with

    @api.depends('text_pattern_expected')
    def _compute_text_pattern_length(self):
        """Calcula la longitud del patrón esperado"""
        for record in self:
            record.text_pattern_length = len(record.text_pattern_expected or '')

    @api.depends('nominal_value', 'tolerance', 'min_value_manual', 'max_value_manual', 'use_manual_range')
    def _compute_min_max(self):
        """Calcula min/max desde nominal y tolerancia, o usa valores manuales"""
        for record in self:
            if record.use_manual_range:
                record.min_value = record.min_value_manual
                record.max_value = record.max_value_manual
            else:
                record.min_value = record.nominal_value - record.tolerance
                record.max_value = record.nominal_value + record.tolerance

    @api.depends('min_value', 'max_value', 'uom_id')
    def _compute_range_display(self):
        """Genera texto de rango para mostrar"""
        for record in self:
            if record.evaluation_type == 'numeric_range':
                uom_name = record.uom_id.name if record.uom_id else ''
                record.range_display = f'{record.min_value}-{record.max_value} {uom_name}'.strip()
            else:
                record.range_display = ''

    @api.depends('active', 'evaluation_type', 'nominal_value', 'tolerance', 'range_display',
                 'text_pattern_expected', 'binary_option_pass')
    def _compute_config_summary(self):
        """Genera resumen de la configuración"""
        for record in self:
            if not record.active:
                record.config_summary = 'Inactiva'
            elif record.evaluation_type == 'numeric_range':
                if record.nominal_value:
                    record.config_summary = f'{record.nominal_value}±{record.tolerance}'
                else:
                    record.config_summary = record.range_display or 'Sin configurar'
            elif record.evaluation_type == 'text_pattern':
                record.config_summary = record.text_pattern_expected or 'Sin configurar'
            elif record.evaluation_type == 'binary_selection':
                record.config_summary = record.binary_option_pass or 'Sin configurar'
            elif record.evaluation_type == 'checkbox_combined':
                if record.checkbox_label_1:
                    record.config_summary = f'{record.checkbox_label_1[:15]}...' if len(record.checkbox_label_1 or '') > 15 else record.checkbox_label_1
                else:
                    record.config_summary = 'Sin configurar'
            else:
                record.config_summary = 'Configurada'

    # ========== Onchange ==========

    @api.onchange('nominal_value', 'tolerance')
    def _onchange_nominal_tolerance(self):
        """Recalcula min/max al cambiar nominal o tolerancia"""
        if not self.use_manual_range:
            self.min_value = self.nominal_value - self.tolerance
            self.max_value = self.nominal_value + self.tolerance

    @api.onchange('use_manual_range')
    def _onchange_use_manual_range(self):
        """Al cambiar modo de rango, actualiza valores"""
        if self.use_manual_range:
            # Copiar valores calculados a manuales
            self.min_value_manual = self.min_value
            self.max_value_manual = self.max_value

    # ========== Métodos de Evaluación ==========

    def evaluate_result(self, result_data):
        """
        Evalúa un resultado usando la configuración de esta especificación.
        
        Wrapper que agrega los valores de configuración (min/max) a result_data
        y delega la evaluación a la especificación.

        Args:
            result_data: Dictionary con datos del resultado

        Returns:
            dict: {'verdict': str, 'message': str}
        """
        self.ensure_one()

        if not self.active:
            return {'verdict': 'not_applicable', 'message': 'Especificación no activa para este producto'}

        # Agregar configuración de rango si es numeric_range
        if self.evaluation_type == 'numeric_range':
            result_data = dict(result_data)
            result_data['min'] = self.min_value
            result_data['max'] = self.max_value

        return self.specification_id.evaluate_result(result_data)

    def get_test_line_detail_values(self, test_line_id):
        """
        Prepara los valores para crear una línea de detalle en el QC.
        Usa los valores configurados para este producto (self), no los de la especificación base.
        
        Args:
            test_line_id: ID de la línea de test padre

        Returns:
            dict: Valores para amunet.quality.test.line.detail
        """
        self.ensure_one()
        
        values = {
            'test_line_id': test_line_id,
            'specification_config_id': self.id,
            'sequence': self.sequence,
            'name': self.specification_id.name or self.specification_name,
            'acceptance_criteria': self.acceptance_criteria,
            'evaluation_type': self.evaluation_type,
            
            # Configuración de evaluación numérica
            'min_value': self.min_value,
            'max_value': self.max_value,
            'uom_id': self.uom_id.id if self.uom_id else False,
            
            # Opciones binarias (desde config)
            'expected_value_binary': self.binary_option_pass,
            'binary_option_pass': self.binary_option_pass,
            'binary_option_fail': self.binary_option_fail,
            
            # Checkboxes (desde config)
            'checkbox_label_1': self.checkbox_label_1,
            'checkbox_label_2': self.checkbox_label_2,
            
            # Text pattern (desde config)
            'text_pattern_expected': self.text_pattern_expected,
            'text_pattern_regex': self.text_pattern_regex,
            'text_phrase_mapping': self.text_phrase_mapping,
            
            # Expected vs Obtained (desde config)
            'expected_options': self.expected_options,
            'obtained_options': self.obtained_options,
            
            # Binary with notes (desde config)
            'binary_notes_option_pass': self.binary_notes_option_pass,
            'binary_notes_option_fail': self.binary_notes_option_fail,
            
            # Ternary (desde config)
            'ternary_option_yes': self.ternary_option_yes,
            'ternary_option_no': self.ternary_option_no,
            'ternary_option_na': self.ternary_option_na,
        }
        
        return values

    # ========== Métodos de Acción ==========

    def action_configure(self):
        """Abre el formulario de configuración de esta especificación"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Configurar: {self.specification_name}',
            'res_model': 'amunet.quality.parameter.specification.config',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'form_view_ref': 'amunet_quality.view_specification_config_form'},
        }

    # ========== Constraints ==========

    @api.constrains('nominal_value', 'tolerance', 'min_value', 'max_value')
    def _check_range(self):
        """Valida que min <= max para rangos numéricos"""
        for record in self:
            if record.evaluation_type == 'numeric_range':
                if record.min_value > record.max_value:
                    raise ValidationError(
                        f'El valor mínimo ({record.min_value}) no puede ser mayor al máximo ({record.max_value})'
                    )

    @api.constrains('product_parameter_rel_id', 'specification_id')
    def _check_unique_spec_per_rel(self):
        """Valida que no haya duplicados de especificación en la misma relación"""
        for record in self:
            duplicates = self.search([
                ('product_parameter_rel_id', '=', record.product_parameter_rel_id.id),
                ('specification_id', '=', record.specification_id.id),
                ('id', '!=', record.id),
            ])
            if duplicates:
                raise ValidationError(
                    f'La especificación "{record.specification_id.name}" ya está configurada para este parámetro'
                )

