# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class AmunetQualityTestLine(models.Model):
    """
    Línea de Prueba/Determinación del Control de Calidad.

    Cada línea representa una prueba individual (parámetro) que debe realizarse
    como parte del control de calidad. Puede contener múltiples detalles
    (uno por especificación activa del parámetro).

    Epic-031: Sistema de Parámetros de Calidad Jerárquicos
    HU-031-2: Ejecutar Control de Calidad con Parámetros Compuestos
    """
    _name = 'amunet.quality.test.line'
    _description = 'Línea de Prueba de Calidad'
    _order = 'sequence, id'

    # ========== Relación con QC ==========

    check_id = fields.Many2one(
        'amunet.quality.check',
        string='Control de calidad',
        required=True,
        ondelete='cascade',
        index=True
    )

    change_reason = fields.Char(
        string='Razón de cambio',
        help='Justificación para cambios en el resultado'
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )

    # ========== Referencia al Parámetro ==========

    parameter_id = fields.Many2one(
        'amunet.quality.check.parameter',
        string='Parámetro',
        ondelete='restrict',
        help='Referencia al parámetro del catálogo'
    )

    parameter_rel_id = fields.Many2one(
        'amunet.quality.parameter.product.rel',
        string='Relación Producto-Parámetro',
        ondelete='restrict',
        help='Referencia a la configuración del parámetro en el producto'
    )

    # ========== Campos de la Prueba (copiados del parámetro) ==========

    name = fields.Char(
        string='Determinación',
        required=False,
        help='Nombre de la prueba'
    )

    code = fields.Char(
        string='Código',
        related='parameter_id.code',
        store=True
    )

    # ========== Detalles (NUEVO en Epic-031) ==========

    detail_line_ids = fields.One2many(
        'amunet.quality.test.line.detail',
        'test_line_id',
        string='Detalles',
        help='Resultados por especificación'
    )

    has_details = fields.Boolean(
        string='Tiene Detalles',
        compute='_compute_detail_counts',
        store=True
    )

    detail_count = fields.Integer(
        string='Total Especificaciones',
        compute='_compute_detail_counts',
        store=True
    )

    detail_pass_count = fields.Integer(
        string='Especificaciones que Cumplen',
        compute='_compute_detail_counts',
        store=True
    )

    detail_fail_count = fields.Integer(
        string='Especificaciones que No Cumplen',
        compute='_compute_detail_counts',
        store=True
    )

    detail_pending_count = fields.Integer(
        string='Especificaciones Pendientes',
        compute='_compute_detail_counts',
        store=True
    )

    detail_na_count = fields.Integer(
        string='Especificaciones N/A',
        compute='_compute_detail_counts',
        store=True
    )

    verdict_summary = fields.Char(
        string='Resumen',
        compute='_compute_verdict_summary',
        store=True
    )

    # ========== Dictamen ==========

    verdict = fields.Selection([
        ('pending', 'Pendiente'),
        ('pass', 'Cumple'),
        ('fail', 'No Cumple'),
        ('not_applicable', 'No Aplica'),
    ], string='Dictamen', compute='_compute_verdict', store=True,
        help='Resultado de la evaluación')

    evaluation_type = fields.Selection([
        ('binary_selection', 'Selección binaria'),
        ('numeric_range', 'Rango numérico'),
        ('checkbox_combined', 'Checkboxes combinados'),
        ('conditional_numeric_range', 'Rango numérico condicional'),
        ('text_pattern', 'Texto con patrón'),
        ('expected_vs_obtained', 'Comparación esperado vs obtenido'),
        ('binary_with_notes', 'Binario con notas'),
        ('ternary_with_na', 'Ternario con N/A'),
        ('decision_matrix', 'Matriz de decisión'),
        ('mavi_07', 'MAVI-07: Visualización de Líneas Resultado'),
        ('vama_034', 'VAMA-034: 2 Pasos (Negativo/Positivo)'),
        ('vama_006', 'VAMA-006: Escala de Color 0-14'),
        ('vama_067', 'VAMA-067: Selección 2 Pasos (Partículas/Color)'),
        ('multi_condition_numeric', 'Multi-Condición Numérica (VAMA-096)'),
        ('vama_044', 'VAMA-044: Funcionalidad de Tubo (4 condiciones)'),
        ('vama_112', 'VAMA-112: Multi-Checkbox Centrífuga'),
        ('vama_078', 'VAMA-078: Multi-Visual Liofilizado'),
        ('mavi_15_ternary', 'MAVI-15: Selección Ternaria'),
    ], string='Tipo de evaluación')

    # ========== Campos de Resultado (Mirroring Detail for consistency) ==========
    acceptance_criteria = fields.Text(string='Criterio de aceptación')
    uom_id = fields.Many2one('uom.uom', string='Unidad de medida')
    min_value = fields.Float(string='Valor mínimo')
    max_value = fields.Float(string='Valor máximo')
    
    result_selection = fields.Char(string='Resultado (Selección)')
    result_numeric = fields.Float(string='Resultado (Numérico)')
    result_display = fields.Char(string='Resultado (Display)')
    result_notes = fields.Text(string='Notas del resultado')
    
    # Binary / Checkboxes
    binary_option_pass = fields.Char(string='Opción Correcta')
    binary_option_fail = fields.Char(string='Opción Incorrecta')
    result_binary_option = fields.Char(string='Resultado Binario')
    checkbox_label_1 = fields.Char(string='Label Checkbox 1')
    checkbox_label_2 = fields.Char(string='Label Checkbox 2')
    result_checkbox_1 = fields.Boolean(string='Resultado Checkbox 1')
    result_checkbox_2 = fields.Boolean(string='Resultado Checkbox 2')
    checkbox_result_confirmed = fields.Boolean(string='Confirmado')

    # Specific widgets
    vama034_sample_type = fields.Selection([('negative', 'Negativa'), ('positive', 'Positiva')], string='VAMA-034: Muestra')
    vama034_observed_result = fields.Selection([('negative', 'Negativa'), ('positive', 'Positiva')], string='VAMA-034: Obs')
    
    mavi15_result = fields.Selection([('opcion_a', 'Opción A'), ('opcion_b', 'Opción B'), ('opcion_c', 'Opción C')], string='MAVI-15')
    
    mga0981_vol_declarado = fields.Char(string='MGA-0981: Declarado')
    mga0981_vol_obtenido = fields.Float(string='MGA-0981: Obtenido')
    
    vama105_nominal_vol = fields.Char(string='VAMA-105: Nominal')
    vama105_measured_vol = fields.Float(string='VAMA-105: Medido')

    mavi11_target_height = fields.Char(string='MAVI-11: Objetivo')
    mavi11_measured_height = fields.Float(string='MAVI-11: Medida')
    
    mavi07_sample_type = fields.Char(string='MAVI-07: Muestra')
    mavi07_expected_result = fields.Char(string='MAVI-07: Esperado')
    
    multi_check_results_json = fields.Text(string='Multi-Check JSON')
    verdict_message = fields.Text(string='Mensaje de dictamen')

    # Add other missing placeholders as needed to fulfill XML requirements
    result_ternary = fields.Char(string='Resultado Ternario')
    result_text_pattern = fields.Char(string='Resultado Patrón')
    text_pattern_expected = fields.Char(string='Patrón Esperado')
    text_phrase_mapping = fields.Text(string='Mapeo Frases')
    result_expected_type = fields.Char(string='Tipo Esperado')
    result_obtained_type = fields.Char(string='Tipo Obtenido')
    
    # Decision Matrix
    result_dm_step1_concentration = fields.Float(string='Conc. DM')
    result_dm_step2_1_control_visible = fields.Boolean(string='Control visible DM')
    result_dm_step2_2_comparison = fields.Selection([('compatible', 'Compatible'), ('incompatible', 'Incompatible')], string='Comp. DM')
    dm_matched_scenario_id = fields.Many2one('amunet.quality.parameter.decision.matrix', string='Escenario DM')
    dm_step2_1_unlocked = fields.Boolean(string='Paso 2.1 Desbloqueado')
    dm_step2_2_unlocked = fields.Boolean(string='Paso 2.2 Desbloqueado')

    # VAMA-044
    vama044_num_gotas = fields.Integer(string='Num. Gotas VAMA-044')
    vama044_num_gotas_min = fields.Integer(string='Min Gotas VAMA-044')
    vama044_vol_gota = fields.Float(string='Vol. Gota VAMA-044')
    vama044_vol_gota_min = fields.Float(string='Min Vol Gota VAMA-044')
    vama044_vol_gota_max = fields.Float(string='Max Vol Gota VAMA-044')
    vama044_union = fields.Selection([('pass', 'Pasa'), ('fail', 'Falla')], string='Unión VAMA-044')
    vama044_vol_llenado = fields.Float(string='Vol. Llenado VAMA-044')
    vama044_vol_llenado_min = fields.Float(string='Min Vol Llenado VAMA-044')
    vama044_vol_llenado_max = fields.Float(string='Max Vol Llenado VAMA-044')

    # VAMA-112
    vama112_cond1 = fields.Boolean(string='Cond 1 VAMA-112')
    vama112_cond2 = fields.Boolean(string='Cond 2 VAMA-112')
    vama112_cond3 = fields.Boolean(string='Cond 3 VAMA-112')
    vama112_cond4 = fields.Boolean(string='Cond 4 VAMA-112')
    vama112_cond5 = fields.Boolean(string='Cond 5 VAMA-112')

    # VAMA-078
    vama078_color = fields.Char(string='Color VAMA-078')
    vama078_forma = fields.Char(string='Forma VAMA-078')
    vama078_textura = fields.Char(string='Textura VAMA-078')
    vama078_humedad = fields.Char(string='Humedad VAMA-078')

    # Multi Cond
    multi_cond_binary = fields.Char(string='Multi Cond Bin')
    multi_cond_num1_min = fields.Float(string='Multi Cond Num1 Min')
    multi_cond_num2_min = fields.Float(string='Multi Cond Num2 Min')
    multi_cond_num2_max = fields.Float(string='Multi Cond Num2 Max')

    # MAVI-07 HM
    mavi07_hm_sample_type = fields.Char(string='MAVI-07 HM Muestra')
    mavi07_hm_result = fields.Char(string='MAVI-07 HM Resultado')

    verdict_display = fields.Char(
        string='Dictamen (Display)',
        compute='_compute_verdict_display'
    )

    # ========== Métodos Computados ==========

    @api.depends('detail_line_ids', 'detail_line_ids.verdict')
    def _compute_detail_counts(self):
        """Cuenta los detalles por estado de dictamen"""
        for record in self:
            details = record.detail_line_ids
            record.has_details = bool(details)
            record.detail_count = len(details)
            record.detail_pass_count = len(details.filtered(lambda d: d.verdict == 'pass'))
            record.detail_fail_count = len(details.filtered(lambda d: d.verdict == 'fail'))
            record.detail_pending_count = len(details.filtered(lambda d: d.verdict == 'pending'))
            record.detail_na_count = len(details.filtered(lambda d: d.verdict == 'not_applicable'))

    @api.depends('detail_pass_count', 'detail_fail_count', 'detail_count', 'detail_na_count', 'verdict')
    def _compute_verdict_summary(self):
        """Genera resumen del dictamen: '3/4 ✅'"""
        for record in self:
            if record.has_details:
                # Conteo efectivo (excluyendo N/A)
                effective_total = record.detail_count - record.detail_na_count
                
                if effective_total == 0:
                    record.verdict_summary = 'N/A'
                elif record.verdict == 'pass':
                    record.verdict_summary = f'{record.detail_pass_count}/{effective_total} ✅'
                elif record.verdict == 'fail':
                    record.verdict_summary = f'{record.detail_pass_count}/{effective_total} ❌'
                elif record.verdict == 'pending':
                    completed = record.detail_pass_count + record.detail_fail_count
                    record.verdict_summary = f'{completed}/{effective_total} ⏳'
                else:
                    record.verdict_summary = 'N/A'
            else:
                # Sin detalles, mostrar simple
                if record.verdict == 'pass':
                    record.verdict_summary = '✅'
                elif record.verdict == 'fail':
                    record.verdict_summary = '❌'
                elif record.verdict == 'pending':
                    record.verdict_summary = '⏳'
                else:
                    record.verdict_summary = ''

    @api.depends(
        'has_details', 'detail_line_ids', 'detail_line_ids.verdict',
        'detail_pass_count', 'detail_fail_count', 'detail_pending_count', 'detail_na_count'
    )
    def _compute_verdict(self):
        """Evalúa automáticamente el resultado desde detalles jerárquicos"""
        for record in self:
            record.verdict = record._compute_verdict_from_details()

    def _compute_verdict_from_details(self):
        """Calcula dictamen agregando los dictámenes de los detalles"""
        self.ensure_one()

        if not self.detail_line_ids:
            return 'pending'

        # Conteos
        fail_count = self.detail_fail_count
        pass_count = self.detail_pass_count
        pending_count = self.detail_pending_count
        na_count = self.detail_na_count
        total_count = self.detail_count

        # Conteo efectivo (excluyendo N/A)
        effective_total = total_count - na_count

        # Lógica de agregación con N/A
        if effective_total == 0:
            # Todas las especificaciones son N/A
            return 'not_applicable'
        elif fail_count > 0:
            return 'fail'
        elif pending_count > 0:
            return 'pending'
        elif pass_count == effective_total:
            return 'pass'
        else:
            return 'pending'

    @api.depends('verdict')
    def _compute_verdict_display(self):
        """Genera texto de dictamen para mostrar"""
        verdict_labels = {
            'pending': '⏳ Pendiente',
            'pass': '✅ Cumple',
            'fail': '❌ No Cumple',
            'not_applicable': '⚪ N/A',
        }
        for record in self:
            record.verdict_display = verdict_labels.get(record.verdict, '⏳ Pendiente')

    # ========== Onchange ==========

    @api.onchange('parameter_id')
    def _onchange_parameter_id(self):
        """
        Copia los datos del parámetro al seleccionarlo.
        
        NOTA: Los campos legacy (specification, test_type, min_value, max_value,
        selection_options, expected_value) fueron eliminados en Epic-031.
        La información ahora está en specification_line_ids del parámetro.
        """
        if self.parameter_id:
            self.name = self.parameter_id.name
            # Los detalles se generan automáticamente desde specification_line_ids
            # mediante generate_detail_lines() cuando se crea el QC

    # ========== Métodos de Creación/Actualización ==========

    @api.model_create_multi
    def create(self, vals_list):
        """Llena automáticamente el name si hay parameter_id pero no name"""
        for vals in vals_list:
            if vals.get('parameter_id') and not vals.get('name'):
                parameter = self.env['amunet.quality.check.parameter'].browse(vals['parameter_id'])
                if parameter:
                    vals['name'] = parameter.name
        return super().create(vals_list)



    # ========== Constraints ==========

    @api.constrains('name', 'parameter_id')
    def _check_name_or_parameter(self):
        """Valida que al menos name o parameter_id esté presente"""
        for record in self:
            if not record.name and not record.parameter_id:
                raise ValidationError(
                    'Debe especificar un parámetro o ingresar manualmente el nombre de la determinación.'
                )

    # ========== Métodos de Generación de Detalles ==========

    def generate_detail_lines(self):
        """
        Genera líneas de detalle desde las especificaciones activas del parámetro.
        
        Este método se llama después de crear la línea de test para generar
        los detalles basados en las especificaciones configuradas para el producto.
        """
        self.ensure_one()

        if self.detail_line_ids:
            return  # Ya tiene detalles

        if not self.parameter_rel_id:
            # Intentar generar directamente desde las especificaciones del parámetro
            if self.parameter_id and self.parameter_id.specification_line_ids:
                self._generate_details_from_parameter()
            return

        # Asegurar que las configuraciones existan
        if not self.parameter_rel_id.specification_config_ids:
            self.parameter_rel_id._generate_specification_configs()

        DetailLine = self.env['amunet.quality.test.line.detail']
        
        detail_vals = []
        for config in self.parameter_rel_id.get_active_specifications():
            vals = config.get_test_line_detail_values(self.id)
            detail_vals.append(vals)

        if detail_vals:
            DetailLine.create(detail_vals)

    def _generate_details_from_parameter(self):
        """
        Genera detalles directamente desde las especificaciones del parámetro.
        Usado cuando no hay configuración de producto (parameter_rel_id).
        """
        self.ensure_one()
        
        if not self.parameter_id:
            return
        
        DetailLine = self.env['amunet.quality.test.line.detail']
        
        detail_vals = []
        for spec in self.parameter_id.specification_line_ids.filtered(lambda s: s.active):
            vals = {
                'test_line_id': self.id,
                'sequence': spec.sequence,
                'name': spec.name,
                'acceptance_criteria': spec.acceptance_criteria,
                'evaluation_type': spec.evaluation_type,
                
                # Configuración de evaluación
                'uom_id': spec.uom_id.id if spec.uom_id else False,
                
                # Opciones binarias
                'expected_value_binary': spec.binary_option_pass,
                'binary_option_pass': spec.binary_option_pass,
                'binary_option_fail': spec.binary_option_fail,
                
                # Checkboxes
                'checkbox_label_1': spec.checkbox_label_1,
                'checkbox_label_2': spec.checkbox_label_2,
                
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
                
                # Ternary
                'ternary_option_yes': spec.ternary_option_yes,
                'ternary_option_no': spec.ternary_option_no,
                'ternary_option_na': spec.ternary_option_na,
            }
            detail_vals.append(vals)
        
        if detail_vals:
            DetailLine.create(detail_vals)

    def action_open_details(self):
        """
        Abre el formulario de detalles para registrar resultados.
        """
        self.ensure_one()
        return {
            'name': f'Registrar: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.quality.test.line',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('amunet_quality.view_amunet_quality_test_line_form_with_details').id,
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit'},
        }

    def action_regenerate_details(self):
        """
        Regenera los detalles de especificación para esta línea.
        Útil si se modificó el parámetro después de crear el QC.
        """
        self.ensure_one()
        
        # Eliminar detalles existentes
        self.detail_line_ids.unlink()
        
        # Regenerar
        self.generate_detail_lines()
        
        return True

    # ========== Métodos de Utilidad ==========

    def get_failed_details(self):
        """Retorna los detalles que fallaron"""
        self.ensure_one()
        return self.detail_line_ids.filtered(lambda d: d.verdict == 'fail')

    def get_pending_details(self):
        """Retorna los detalles pendientes"""
        self.ensure_one()
        return self.detail_line_ids.filtered(lambda d: d.verdict == 'pending')

    def is_complete(self):
        """
        Verifica si todos los detalles tienen resultado.
        
        NOTA: Los campos legacy (test_type, result_numeric, result_selection)
        fueron eliminados en Epic-031. Ahora se usa el sistema de detalles.
        """
        self.ensure_one()
        if self.has_details:
            # Con sistema jerárquico: verificar que todos los detalles estén completos
            return self.detail_pending_count == 0
        else:
            # Sin detalles: línea simple (legacy o parámetro sin especificaciones)
            # En este caso, la línea se considera completa si tiene dictamen
            return self.verdict != 'pending'

    def write(self, vals):
        """
        Audit Log para cambios en resultados de pruebas.
        También llena automáticamente el name si se asigna parameter_id pero no name.
        """
        # Logic from first write method: Name autofill
        if 'parameter_id' in vals and 'name' not in vals:
            parameter_id = vals.get('parameter_id')
            if parameter_id:
                parameter = self.env['amunet.quality.check.parameter'].browse(parameter_id)
                if parameter:
                    vals['name'] = parameter.name
        TRACKED_FIELDS = ['verdict', 'verdict_display']
        tracked_in_vals = [f for f in TRACKED_FIELDS if f in vals]

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
                    old_val = old_values.get((record.id, field))
                    new_val = record[field] or ''
                    
                    if str(old_val) != str(new_val):
                        AuditLog.create({
                            'model_name': 'amunet.quality.test.line',
                            'res_id': record.id,
                            'res_name': f"{record.check_id.name} - {record.name}",
                            'field_name': field,
                            'old_value': str(old_val),
                            'new_value': str(new_val),
                            'justification': vals.get('change_reason') or record.change_reason or 'Actualización de resultado',
                            'user_id': self.env.user.id,
                        })
                # Limpiar razón de cambio
                if record.change_reason:
                    record.sudo().write({'change_reason': False})

        return result

    def unlink(self):
        """Prevent deletion of Test Lines once the QC is out of 'draft' state."""
        for record in self:
            if record.check_id.state != 'draft':
                raise UserError(_("No se pueden eliminar líneas de prueba si el control de calidad no está en estado 'Borrador'."))
        return super().unlink()
