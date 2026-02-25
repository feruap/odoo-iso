# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import json
import re


class AmunetQualityParameterSpecification(models.Model):
    """
    Especificación de Parámetro de Calidad.

    Representa una línea de especificación dentro de un parámetro.
    Cada parámetro puede tener múltiples especificaciones (ej: MAVI-04 tiene 4).

    Epic-031: Sistema de Parámetros de Calidad Jerárquicos
    HU-031-1: Configurar Plantillas de Parámetros con Especificaciones
    """
    _name = 'amunet.quality.check.parameter.specification'
    _description = 'Especificación de Parámetro de Calidad'
    _order = 'sequence, id'

    # ========== Relación con Parámetro ==========

    parameter_id = fields.Many2one(
        'amunet.quality.check.parameter',
        string='Parámetro',
        required=True,
        ondelete='cascade',
        index=True
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de la especificación dentro del parámetro'
    )

    # ========== Identificación ==========

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre de la especificación (ej: Polvo, Ancho, Largo)'
    )

    acceptance_criteria = fields.Char(
        string='Criterio de aceptación',
        help='Descripción del criterio de aceptación (ej: Sin polvo, 60 ±1 mm)'
    )

    # ========== Tipo de Evaluación ==========

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
    ], string='Tipo de evaluación', required=True, default='binary_selection',
        help='Define cómo se evaluará el resultado de esta especificación')

    # ========== Configuración Binary Selection ==========

    binary_prefix = fields.Char(
        string='Prefijo',
        help='Prefijo para opciones binarias (ej: Sin, Presencia, Sellado)'
    )

    binary_suffix = fields.Char(
        string='Sufijo',
        help='Sufijo para opciones binarias (ej: polvo, manchas, colorante)'
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

    uom_id = fields.Many2one(
        'uom.uom',
        string='Unidad de medida',
        help='Unidad de medida para valores numéricos (ej: mm, ml, g)'
    )

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

    # ========== Configuración Conditional Numeric Range ==========

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

    # ========== Configuración Conditional Numeric Range ==========

    conditional_option_ids = fields.One2many(
        'amunet.quality.parameter.conditional.option',
        'specification_id',
        string='Opciones condicionales',
        help='Opciones de volumen/rango para evaluación condicional'
    )

    conditional_option_count = fields.Integer(
        string='Cantidad de opciones',
        compute='_compute_conditional_option_count',
        store=True
    )

    # ========== Configuración Text Pattern (VAMA-112) ==========

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
        help='''JSON con mapeo de posiciones a frases.
Formato:
{
    "positions": [
        {"index": 0, "A": "adecuado", "B": "no adecuado", "context": "El funcionamiento es {value}"},
        ...
    ],
    "phrase_template": "El funcionamiento de la centrífuga es {0}, {1} de movimientos bruscos..."
}'''
    )

    # ========== Configuración Expected vs Obtained (VAMA-032) ==========

    expected_options = fields.Char(
        string='Opciones esperadas',
        help='Opciones para tipo esperado, separadas por coma (ej: Positivo,Negativo)'
    )

    obtained_options = fields.Char(
        string='Opciones obtenidas',
        help='Opciones para resultado obtenido, separadas por coma (ej: Positivo,Negativo)'
    )

    # ========== Configuración Binary with Notes (VAMA-063) ==========

    binary_notes_option_pass = fields.Char(
        string='Opción que cumple (con notas)',
        help='Texto de la opción que cumple (ej: La información es completa y correcta)'
    )

    binary_notes_option_fail = fields.Char(
        string='Opción que no cumple (con notas)',
        help='Texto de la opción que no cumple (ej: La información es incompleta)'
    )

    binary_notes_required = fields.Boolean(
        string='Notas requeridas si no cumple',
        default=True,
        help='Si está activo, las notas son obligatorias cuando se selecciona la opción que no cumple'
    )

    # ========== Configuración Ternary with N/A (MAVI-14) ==========

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

    # ========== Configuración Decision Matrix (MAVI-16) ==========

    decision_matrix_scenario_ids = fields.One2many(
        'amunet.quality.parameter.decision.matrix',
        'specification_id',
        string='Escenarios de matriz',
        help='Escenarios de la matriz de decisión para evaluación multi-paso'
    )

    decision_matrix_scenario_count = fields.Integer(
        string='Cantidad de escenarios',
        compute='_compute_decision_matrix_scenario_count',
        store=True
    )

    # Etiquetas personalizables para los pasos
    dm_step1_label = fields.Char(
        string='Etiqueta paso 1',
        default='Concentración objetivo',
        help='Etiqueta para el primer paso (Paso 1)'
    )

    dm_step2_1_label = fields.Char(
        string='Etiqueta paso 2.1',
        default='Línea de control (C) visible',
        help='Etiqueta para el paso 2.1 (validador)'
    )

    dm_step2_2_label = fields.Char(
        string='Etiqueta paso 2.2',
        default='Comparación visual T vs R',
        help='Etiqueta para el paso 2.2 (comparación)'
    )

    # ========== Control ==========

    active = fields.Boolean(
        string='Activo',
        default=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        related='parameter_id.company_id',
        store=True
    )

    change_reason = fields.Char(
        string='Razón de cambio',
        help='Justificación obligatoria para cambios en la especificación'
    )

    # ========== Métodos de Auditoría & Integridad ==========

    def write(self, vals):
        """
        Registra cambios en la especificación en el Audit Log.
        Exige justificante si se cambian campos críticos.
        """
        from odoo.exceptions import UserError
        from odoo import _

        TRACKED_FIELDS = ['name', 'acceptance_criteria', 'evaluation_type', 'nominal_value', 'tolerance', 'min_value', 'max_value', 'active']
        tracked_in_vals = [f for f in TRACKED_FIELDS if f in vals]

        if tracked_in_vals:
            for record in self:
                # Assuming 'state' field exists and indicates draft status
                # If state is not 'draft' and a tracked field is being changed without a change_reason, raise an error
                if hasattr(record, 'state') and record.state != 'draft' and not (vals.get('change_reason') or record.change_reason):
                    for field in tracked_in_vals:
                        # Check if the value for the tracked field is actually changing
                        if field in vals and record[field] != vals[field]:
                            raise UserError(_("Se requiere una 'Razón de cambio' para modificar especificaciones que no están en estado Borrador."))

        # Snapshot de valores viejos
        old_values = {}
        if tracked_in_vals:
            for record in self:
                for field in tracked_in_vals:
                    val = record[field]
                    if hasattr(val, 'display_name'):
                        old_values[(record.id, field)] = val.display_name or str(val.id)
                    elif hasattr(val, 'name'):
                        old_values[(record.id, field)] = val.name
                    else:
                        old_values[(record.id, field)] = str(val)

        # Ejecutar escritura estándar usando super() moderno
        result = super().write(vals)

        if result and tracked_in_vals:
            AuditLog = self.env['amunet.quality.audit.log']
            for record in self:
                for field in tracked_in_vals:
                    old_val_str = old_values.get((record.id, field))
                    new_val = record[field]
                    
                    if hasattr(new_val, 'display_name'):
                        new_val_str = new_val.display_name or str(new_val.id)
                    elif hasattr(new_val, 'name'):
                        new_val_str = new_val.name
                    else:
                        new_val_str = str(new_val)

                    if old_val_str != new_val_str:
                        AuditLog.create({
                            'model_name': 'amunet.quality.check.parameter.specification',
                            'res_id': record.id,
                            'res_name': record.display_name,
                            'field_name': field,
                            'old_value': old_val_str,
                            'new_value': new_val_str,
                            'justification': vals.get('change_reason') or record.change_reason or 'Cambio de configuración',
                            'user_id': self.env.user.id,
                        })
                # Limpiar razón de cambio
                if record.change_reason:
                    record.sudo().write({'change_reason': False})
        return result

    def unlink(self):
        """No permitir borrar especificaciones (Data Integrity)."""
        from odoo.exceptions import ValidationError
        from odoo import _
        if not self.env.context.get('install_mode') and not self.env.su:
            raise ValidationError(_("No se permite eliminar especificaciones para mantener la integridad del registro histórico. Por favor, archívelas (active=False) en su lugar."))
        return super().unlink()

    # ========== Campos Computados ==========

    display_name = fields.Char(
        string='Nombre completo',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('parameter_id.code', 'parameter_id.name', 'name')
    def _compute_display_name(self):
        """Genera nombre completo: [CÓDIGO] Determinación - Especificación"""
        for record in self:
            parts = []
            if record.parameter_id:
                if record.parameter_id.code:
                    parts.append(f"[{record.parameter_id.code}]")
                if record.parameter_id.name:
                    parts.append(record.parameter_id.name)
            if record.name:
                parts.append(f"- {record.name}")
            record.display_name = ' '.join(parts) if parts else record.name or ''

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

    @api.depends('conditional_option_ids')
    def _compute_conditional_option_count(self):
        """Cuenta las opciones condicionales"""
        for record in self:
            record.conditional_option_count = len(record.conditional_option_ids)

    @api.depends('decision_matrix_scenario_ids')
    def _compute_decision_matrix_scenario_count(self):
        """Cuenta los escenarios de la matriz de decisión"""
        for record in self:
            record.decision_matrix_scenario_count = len(record.decision_matrix_scenario_ids)

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

    # ========== Métodos de Acción ==========

    def action_open_configuration(self):
        """Abre el formulario completo de configuración de la especificación"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Configurar: {self.name}',
            'res_model': 'amunet.quality.check.parameter.specification',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'form_view_ref': 'amunet_quality.view_amunet_quality_specification_form'},
        }

    def action_populate_mavi16_scenarios(self):
        """
        Acción para poblar la matriz con los 13 escenarios por defecto de MAVI-16.
        Se llama desde el botón en la vista de especificación.
        """
        self.ensure_one()
        if self.evaluation_type != 'decision_matrix':
            return

        # Eliminar escenarios existentes
        self.decision_matrix_scenario_ids.unlink()

        # Obtener escenarios por defecto
        DecisionMatrix = self.env['amunet.quality.parameter.decision.matrix']
        scenarios = DecisionMatrix.get_mavi16_default_scenarios()

        for scenario_vals in scenarios:
            scenario_vals['specification_id'] = self.id
            DecisionMatrix.create(scenario_vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Matriz poblada',
                'message': f'Se crearon {len(scenarios)} escenarios para MAVI-16.',
                'type': 'success',
                'sticky': False,
            }
        }

    def check_ready_for_use(self):
        """
        Verifica que la especificación esté completamente configurada para uso.
        Llamar este método antes de asignar el parámetro a un producto o crear un QC.
        
        Returns:
            tuple: (is_ready: bool, error_message: str or None)
        """
        self.ensure_one()
        
        if self.evaluation_type == 'text_pattern':
            if not self.text_pattern_expected:
                return (False, f'Especificación "{self.name}": Falta configurar el Patrón Esperado')
            if not self.text_pattern_regex:
                return (False, f'Especificación "{self.name}": Falta configurar la Expresión Regular')

        elif self.evaluation_type == 'binary_selection':
            # Requiere al menos binary_prefix configurado (suffix es opcional)
            if not self.binary_prefix:
                return (False, f'Especificación "{self.name}": Falta configurar el Prefijo binario')

        elif self.evaluation_type == 'checkbox_combined':
            if not self.checkbox_label_1 or not self.checkbox_label_2:
                return (False, f'Especificación "{self.name}": Falta configurar etiquetas de checkboxes')
        
        elif self.evaluation_type == 'expected_vs_obtained':
            if not self.expected_options or not self.obtained_options:
                return (False, f'Especificación "{self.name}": Falta configurar opciones esperado/obtenido')
        
        elif self.evaluation_type == 'binary_with_notes':
            if not self.binary_notes_option_pass or not self.binary_notes_option_fail:
                return (False, f'Especificación "{self.name}": Falta configurar opciones de binary con notas')

        elif self.evaluation_type == 'decision_matrix':
            if not self.decision_matrix_scenario_ids:
                return (False, f'Especificación "{self.name}": Falta configurar los escenarios de la matriz de decisión')
            # Verificar que al menos haya un escenario de fallo por línea C no visible
            has_control_fail = any(
                s.step2_1_control_visible == 'no' for s in self.decision_matrix_scenario_ids
            )
            if not has_control_fail:
                return (False, f'Especificación "{self.name}": La matriz debe incluir un escenario de fallo cuando la línea C no es visible')

        return (True, None)

    def is_configured(self):
        """Retorna True si la especificación está completamente configurada"""
        is_ready, _ = self.check_ready_for_use()
        return is_ready

    # ========== Métodos de Evaluación ==========

    def evaluate_result(self, result_data):
        """
        Evalúa un resultado contra la especificación.

        Args:
            result_data: Dictionary con datos del resultado según tipo de evaluación
                - binary_selection: {'selection': 'Sin polvo'}
                - numeric_range: {'numeric': 60.5, 'min': 59, 'max': 61}
                - checkbox_combined: {'checkbox_1': True, 'checkbox_2': True}
                - conditional_numeric_range: {'option_id': 1, 'value': 505.2}
                - text_pattern: {'pattern': 'AAAAA'}
                - expected_vs_obtained: {'expected': 'Positivo', 'obtained': 'Positivo'}
                - binary_with_notes: {'option': 'pass', 'notes': ''}
                - ternary_with_na: {'selection': 'yes'|'no'|'na'}

        Returns:
            dict: {'verdict': 'pass'|'fail'|'pending'|'not_applicable', 'message': str}
        """
        self.ensure_one()

        if not result_data:
            return {'verdict': 'pending', 'message': 'Sin resultado registrado'}

        evaluator = getattr(self, f'_evaluate_{self.evaluation_type}', None)
        if evaluator:
            return evaluator(result_data)

        return {'verdict': 'pending', 'message': 'Tipo de evaluación no soportado'}

    def _evaluate_binary_selection(self, result_data):
        """Evalúa resultado de selección binaria"""
        selection = result_data.get('selection')
        if not selection:
            return {'verdict': 'pending', 'message': 'Seleccione una opción'}

        if selection == self.binary_option_pass:
            return {'verdict': 'pass', 'message': selection}
        else:
            return {'verdict': 'fail', 'message': selection}

    def _evaluate_numeric_range(self, result_data):
        """Evalúa resultado de rango numérico"""
        value = result_data.get('numeric')
        min_val = result_data.get('min')
        max_val = result_data.get('max')

        if value is None:
            return {'verdict': 'pending', 'message': 'Ingrese un valor numérico'}

        if min_val is None or max_val is None:
            return {'verdict': 'pending', 'message': 'Rango no configurado'}

        uom_name = self.uom_id.name if self.uom_id else ''

        if min_val <= value <= max_val:
            return {
                'verdict': 'pass',
                'message': f'{value} {uom_name} (rango: {min_val}-{max_val})'
            }
        else:
            return {
                'verdict': 'fail',
                'message': f'{value} {uom_name} fuera de rango ({min_val}-{max_val})'
            }

    def _evaluate_checkbox_combined(self, result_data):
        """Evalúa resultado de checkboxes combinados"""
        cb1 = result_data.get('checkbox_1', False)
        cb2 = result_data.get('checkbox_2', False)

        if self.checkbox_require_both:
            if cb1 and cb2:
                return {
                    'verdict': 'pass',
                    'message': f'✓ {self.checkbox_label_1}, ✓ {self.checkbox_label_2}'
                }
            else:
                parts = []
                if cb1:
                    parts.append(f'✓ {self.checkbox_label_1}')
                else:
                    parts.append(f'✗ {self.checkbox_label_1}')
                if cb2:
                    parts.append(f'✓ {self.checkbox_label_2}')
                else:
                    parts.append(f'✗ {self.checkbox_label_2}')
                return {'verdict': 'fail', 'message': ', '.join(parts)}
        else:
            # Al menos uno debe estar marcado
            if cb1 or cb2:
                return {'verdict': 'pass', 'message': 'Al menos uno marcado'}
            else:
                return {'verdict': 'fail', 'message': 'Ninguno marcado'}

    def _evaluate_conditional_numeric_range(self, result_data):
        """Evalúa resultado de rango numérico condicional"""
        option_id = result_data.get('option_id')
        value = result_data.get('value')

        if not option_id:
            return {'verdict': 'pending', 'message': 'Seleccione una opción'}

        if value is None:
            return {'verdict': 'pending', 'message': 'Ingrese el valor medido'}

        option = self.env['amunet.quality.parameter.conditional.option'].browse(option_id)
        if not option.exists():
            return {'verdict': 'fail', 'message': 'Opción no válida'}

        uom_name = option.uom_id.name if option.uom_id else ''

        if option.min_value <= value <= option.max_value:
            return {
                'verdict': 'pass',
                'message': f'{value} {uom_name} (opción: {option.name}, rango: {option.min_value}-{option.max_value})'
            }
        else:
            return {
                'verdict': 'fail',
                'message': f'{value} {uom_name} fuera de rango {option.min_value}-{option.max_value} ({option.name})'
            }

    def _evaluate_text_pattern(self, result_data):
        """Evalúa resultado de texto con patrón (VAMA-112)"""
        pattern_input = result_data.get('pattern', '').upper()

        if not pattern_input:
            return {'verdict': 'pending', 'message': 'Ingrese el patrón'}

        # Validar formato con regex
        if self.text_pattern_regex:
            if not re.match(self.text_pattern_regex, pattern_input):
                return {
                    'verdict': 'fail',
                    'message': f'Formato inválido. Use solo caracteres permitidos, longitud {self.text_pattern_length}'
                }

        # Validar longitud
        if len(pattern_input) != self.text_pattern_length:
            return {
                'verdict': 'fail',
                'message': f'Longitud incorrecta. Esperado: {self.text_pattern_length}, Ingresado: {len(pattern_input)}'
            }

        # Construir frase descriptiva
        phrase = self._build_phrase_from_pattern(pattern_input)

        # Comparar con patrón esperado
        if pattern_input == self.text_pattern_expected:
            return {
                'verdict': 'pass',
                'message': phrase,
                'constructed_phrase': phrase
            }
        else:
            # Identificar posiciones que fallan
            failed_positions = self._get_failed_positions(pattern_input)
            return {
                'verdict': 'fail',
                'message': f'{phrase}\n\nPosiciones que no cumplen: {failed_positions}',
                'constructed_phrase': phrase,
                'failed_positions': failed_positions
            }

    def _build_phrase_from_pattern(self, pattern_input):
        """Construye la frase descriptiva desde el patrón ingresado"""
        self.ensure_one()

        if not self.text_phrase_mapping:
            return pattern_input

        try:
            mapping = json.loads(self.text_phrase_mapping)
            positions = mapping.get('positions', [])
            phrase_template = mapping.get('phrase_template', '')

            if phrase_template:
                # Usar template con placeholders
                values = {}
                for pos in positions:
                    idx = pos.get('index', 0)
                    if idx < len(pattern_input):
                        char = pattern_input[idx]
                        values[str(idx)] = pos.get(char, char)

                # Reemplazar placeholders {0}, {1}, etc.
                result = phrase_template
                for key, value in values.items():
                    result = result.replace(f'{{{key}}}', value)
                return result
            else:
                # Construir frase concatenando contextos
                parts = []
                for pos in positions:
                    idx = pos.get('index', 0)
                    if idx < len(pattern_input):
                        char = pattern_input[idx]
                        value = pos.get(char, char)
                        context = pos.get('context', '{value}')
                        parts.append(context.replace('{value}', value))
                return ', '.join(parts)

        except (json.JSONDecodeError, KeyError, TypeError):
            return pattern_input

    def _get_failed_positions(self, pattern_input):
        """Identifica las posiciones donde el patrón no cumple"""
        self.ensure_one()

        failed = []
        expected = self.text_pattern_expected or ''

        for i, (inp, exp) in enumerate(zip(pattern_input, expected)):
            if inp != exp:
                failed.append(str(i + 1))

        return ', '.join(failed) if failed else 'Ninguna'

    def _evaluate_expected_vs_obtained(self, result_data):
        """Evalúa comparación esperado vs obtenido (VAMA-032)"""
        expected = result_data.get('expected')
        obtained = result_data.get('obtained')

        if not expected:
            return {'verdict': 'pending', 'message': 'Seleccione el tipo de muestra'}

        if not obtained:
            return {'verdict': 'pending', 'message': 'Seleccione el resultado obtenido'}

        # Normalizar comparación (quitar espacios, case-insensitive conceptual)
        # Lógica especial: "Muestra Negativa" -> "negativo", "Muestra Positiva" -> "positivo"
        exp_norm = expected.strip().lower()
        if 'negativa' in exp_norm: exp_norm = 'negativo'
        if 'positiva' in exp_norm: exp_norm = 'positivo'
        
        obt_norm = obtained.strip().lower()
        if 'negativa' in obt_norm: obt_norm = 'negativo'
        if 'positiva' in obt_norm: obt_norm = 'positivo'

        if exp_norm == obt_norm:
            return {
                'verdict': 'pass',
                'message': f'Muestra {expected}: {obtained} ✓'
            }
        else:
            return {
                'verdict': 'fail',
                'message': f'El resultado ({obtained}) no coincide con el tipo de muestra ({expected})'
            }

    def _evaluate_binary_with_notes(self, result_data):
        """Evalúa selección binaria con notas (VAMA-063)"""
        option = result_data.get('option')
        notes = result_data.get('notes', '').strip()

        if not option:
            return {'verdict': 'pending', 'message': 'Seleccione una opción'}

        if option == 'pass':
            return {
                'verdict': 'pass',
                'message': self.binary_notes_option_pass or 'Cumple'
            }
        else:
            if self.binary_notes_required and not notes:
                return {
                    'verdict': 'pending',
                    'message': f'{self.binary_notes_option_fail or "No cumple"} - Requiere notas'
                }
            return {
                'verdict': 'fail',
                'message': f'{self.binary_notes_option_fail or "No cumple"}. Nota: {notes}' if notes else (self.binary_notes_option_fail or 'No cumple')
            }

    def _evaluate_ternary_with_na(self, result_data):
        """Evalúa selección ternaria con N/A (MAVI-14)"""
        selection = result_data.get('selection')

        if not selection:
            return {'verdict': 'pending', 'message': 'Seleccione una opción (Sí/No/N/A)'}

        if selection == 'yes':
            return {
                'verdict': 'pass',
                'message': self.ternary_option_yes or 'Sí'
            }
        elif selection == 'no':
            return {
                'verdict': 'fail',
                'message': self.ternary_option_no or 'No'
            }
        elif selection == 'na':
            return {
                'verdict': 'not_applicable',
                'message': f'{self.ternary_option_na or "N/A"} - Excluida del conteo'
            }

        return {'verdict': 'pending', 'message': 'Opción no reconocida'}

    # ========== Métodos Auxiliares ==========

    def get_selection_options(self):
        """
        Obtiene la lista de opciones para widgets de selección.

        Returns:
            list: Lista de tuplas [(value, label), ...]
        """
        self.ensure_one()

        if self.evaluation_type == 'binary_selection':
            return [
                (self.binary_option_pass, self.binary_option_pass),
                (self.binary_option_fail, self.binary_option_fail),
            ]

        elif self.evaluation_type == 'expected_vs_obtained':
            expected_list = [opt.strip() for opt in (self.expected_options or '').split(',') if opt.strip()]
            return [(opt, opt) for opt in expected_list]

        elif self.evaluation_type == 'ternary_with_na':
            return [
                ('yes', self.ternary_option_yes or 'Sí'),
                ('no', self.ternary_option_no or 'No'),
                ('na', self.ternary_option_na or 'N/A'),
            ]

        return []

    def _evaluate_decision_matrix(self, result_data):
        """
        Evalúa resultado de matriz de decisión (MAVI-16).
        Busca el escenario que coincide con los 3 pasos y retorna el dictamen.
        """
        concentration = result_data.get('dm_step1_concentration')
        control_visible = result_data.get('dm_step2_1_control_visible') == 'yes'
        comparison = result_data.get('dm_step2_2_comparison')

        if not concentration:
            return {'verdict': 'pending', 'message': 'Complete el Paso 1 (Concentración)'}
        
        # Validar consistencia de inputs segun logica del widget
        # Si control no es visible, comparison puede ser irrelevante o false
        
        if result_data.get('dm_step2_1_control_visible') is None:
             return {'verdict': 'pending', 'message': 'Complete el Paso 2.1 (Línea Control)'}

        DecisionMatrix = self.env['amunet.quality.parameter.decision.matrix']
        scenarios = DecisionMatrix.find_matching_scenario(
            self.id, concentration, control_visible, comparison
        )

        if not scenarios:
            return {
                'verdict': 'fail', 
                'message': 'Escenario no configurado en la matriz. Revise los inputs.'
            }

        scenario = scenarios[0]
        return {
            'verdict': scenario.verdict,
            'message': scenario.result_message
        }

    # ========== Evaluación VAMA-044 (Funcionalidad Tubo) ==========
    vama044_label_1 = fields.Char(string='Etiqueta 1', default='Integridad')
    vama044_label_2 = fields.Char(string='Etiqueta 2', default='Vacío')
    vama044_label_3 = fields.Char(string='Etiqueta 3', default='Tapón')
    vama044_label_4 = fields.Char(string='Etiqueta 4', default='Etiqueta')

    def _evaluate_vama_044(self, result_data):
        """Evalúa funcionalidad de tubo (4 checks mandatorios)"""
        c1 = result_data.get('vama044_check_1')
        c2 = result_data.get('vama044_check_2')
        c3 = result_data.get('vama044_check_3')
        c4 = result_data.get('vama044_check_4')
        
        if c1 and c2 and c3 and c4:
             return {'verdict': 'pass', 'message': 'Funcionalidad Completa Correcta'}
        return {'verdict': 'fail', 'message': 'Falla en uno o más criterios de funcionalidad'}

    # ========== Evaluación VAMA-112 (Centrífuga) ==========
    def _evaluate_vama_112(self, result_data):
        """Evalúa checklist de centrífuga"""
        noise = result_data.get('vama112_check_noise')
        vibrate = result_data.get('vama112_check_vibration')
        timer = result_data.get('vama112_check_timer')
        speed = result_data.get('vama112_check_speed')
        
        if noise and vibrate and timer and speed:
             return {'verdict': 'pass', 'message': 'Funcionamiento Centrífuga Correcto'}
        return {'verdict': 'fail', 'message': 'Falla en parámetros de centrífuga'}

    # ========== Evaluación VAMA-078 (Multi-Visual) ==========
    def _evaluate_vama_078(self, result_data):
        """Evalúa multi-aspecto visual"""
        color = result_data.get('vama078_check_color')
        texture = result_data.get('vama078_check_texture')
        particles = result_data.get('vama078_check_particles')
        solubility = result_data.get('vama078_check_solubility')
        
        if color and texture and particles and solubility:
            return {'verdict': 'pass', 'message': 'Apariencia Conforme'}
        return {'verdict': 'fail', 'message': 'Defecto visual detectado'}

    # ========== Evaluación MAVI-07 (Líneas Visuales) ==========
    def _evaluate_mavi_07(self, result_data):
        """Evalúa MAVI-07 usando lógica expected vs obtained"""
        return self._evaluate_expected_vs_obtained(result_data)

    # ========== Evaluación Multi-Condición Numérica ==========
    def _evaluate_multi_condition_numeric(self, result_data):
        """
        Evalúa múltiples condiciones numéricas. 
        Asume que result_data viene como lista de {option_id, value}.
        Todas las condiciones activas deben cumplirse.
        """
        # Simplificación: Usa la misma logica de conditional_numeric pero iterando
        # El widget debe enviar un valor por cada option_id
        results = result_data.get('multi_values', {}) # dict {option_id: value}
        if not results:
             return {'verdict': 'pending', 'message': 'Ingrese valores'}

        errors = []
        for option in self.conditional_option_ids:
            val = results.get(str(option.id))
            if val is None:
                errors.append(f'Falta valor para {option.name}')
                continue
            
            try:
                val_float = float(val)
                if not (option.min_value <= val_float <= option.max_value):
                    errors.append(f'{option.name}: {val} fuera de rango ({option.min_value}-{option.max_value})')
            except ValueError:
                errors.append(f'{option.name}: Valor inválido')
        
        if errors:
            return {'verdict': 'fail', 'message': " | ".join(errors)}
        return {'verdict': 'pass', 'message': 'Todas las condiciones cumplen'}


    def get_obtained_options(self):
        """Obtiene opciones para campo 'obtained' en expected_vs_obtained"""
        self.ensure_one()
        if self.evaluation_type == 'expected_vs_obtained':
            obtained_list = [opt.strip() for opt in (self.obtained_options or '').split(',') if opt.strip()]
            return [(opt, opt) for opt in obtained_list]
        return []

    # ========== Constraints ==========

    @api.constrains('evaluation_type', 'binary_prefix', 'binary_suffix')
    def _check_binary_config(self):
        """
        Valida configuración de selección binaria.
        Relajado para permitir creación inicial - validación en check_ready_for_use().
        """
        pass

    @api.constrains('evaluation_type', 'checkbox_label_1', 'checkbox_label_2')
    def _check_checkbox_config(self):
        """
        Valida configuración de checkboxes combinados.
        Relajado para permitir creación inicial - validación en check_ready_for_use().
        """
        pass

    @api.constrains('evaluation_type', 'text_pattern_expected', 'text_pattern_regex')
    def _check_text_pattern_config(self):
        """
        Valida configuración de texto con patrón.
        Solo valida si el campo active está en True (para permitir creación inicial).
        """
        for record in self:
            # Solo validar si está activo (permite crear desactivado y configurar después)
            if record.evaluation_type == 'text_pattern' and record.active:
                # Permitir guardar si al menos tiene el nombre (configuración inicial)
                # La validación estricta se hace al usar el parámetro
                pass  # Validación movida a check_ready_for_use()

    @api.constrains('evaluation_type', 'expected_options', 'obtained_options')
    def _check_expected_vs_obtained_config(self):
        """
        Valida configuración de comparación esperado vs obtenido.
        Relajado para permitir creación inicial - validación en check_ready_for_use().
        """
        pass

    @api.constrains('evaluation_type', 'binary_notes_option_pass', 'binary_notes_option_fail')
    def _check_binary_notes_config(self):
        """
        Valida configuración de binary con notas.
        Relajado para permitir creación inicial - validación en check_ready_for_use().
        """
        pass

    @api.constrains('text_phrase_mapping')
    def _check_json_mapping(self):
        """Valida que el mapeo de frases sea JSON válido"""
        for record in self:
            if record.text_phrase_mapping:
                try:
                    json.loads(record.text_phrase_mapping)
                except json.JSONDecodeError:
                    raise ValidationError(
                        'El mapeo de frases debe ser un JSON válido'
                    )

