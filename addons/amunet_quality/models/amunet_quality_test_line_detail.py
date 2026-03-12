# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import json
import re


class AmunetQualityTestLineDetail(models.Model):
    """
    Detalle de Línea de Prueba de Calidad.

    Representa el resultado de una especificación individual dentro
    de una línea de test. Cada línea de test puede tener múltiples
    detalles (uno por especificación activa).

    Epic-031: Sistema de Parámetros de Calidad Jerárquicos
    HU-031-2: Ejecutar Control de Calidad con Parámetros Compuestos
    """
    _name = 'amunet.quality.test.line.detail'
    _description = 'Detalle de Línea de Prueba de Calidad'
    _order = 'sequence, id'

    # ========== Relaciones ==========

    test_line_id = fields.Many2one(
        'amunet.quality.test.line',
        string='Línea de prueba',
        required=True,
        ondelete='cascade',
        index=True
    )

    check_id = fields.Many2one(
        'amunet.quality.check',
        string='Control de Calidad',
        related='test_line_id.check_id',
        store=True,
        readonly=True
    )

    specification_config_id = fields.Many2one(
        'amunet.quality.parameter.specification.config',
        string='Configuración de especificación',
        ondelete='restrict',
        index=True
    )

    specification_id = fields.Many2one(
        'amunet.quality.check.parameter.specification',
        string='Especificación',
        related='specification_config_id.specification_id',
        store=True
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )

    # ========== Identificación (copiados de especificación) ==========

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre de la especificación (ej: Polvo, Ancho)'
    )

    acceptance_criteria = fields.Char(
        string='Criterio de aceptación',
        help='Criterio de aceptación descriptivo'
    )

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
        ('vama_multi_check', 'VAMA: Multi-Check Genérico (1-6 puntos)'),
        ('mga_0981', 'MGA-0981: Variación de Volumen (± 0.5 ml)'),
        ('vama_105', 'VAMA-105: Volumen Nominal vs Medido'),
        ('mavi_15_ternary', 'MAVI-15: Selección Ternaria'),
        ('mavi_11_height', 'MAVI-11: Altura (6/8 cm ± 0.5)'),
        ('mavi_07_ternary', 'MAVI-07: Ternario (Hojas Maestras)'),
    ], string='Tipo de evaluación', required=True, default='binary_selection')

    # ========== Campos de Resultado ==========

    # -- Binary Selection --
    result_selection = fields.Char(
        string='Resultado (Selección)',
        help='Valor seleccionado para evaluación binaria'
    )

    # -- Numeric Range --
    result_numeric = fields.Float(
        string='Resultado (Numérico)',
        digits='Product Unit of Measure',
        help='Valor numérico medido'
    )
    
    result_numeric_filled = fields.Boolean(
        string='Campo numérico llenado',
        default=False,
        help='Indica si el usuario ya ingresó un valor en result_numeric'
    )

    # -- Checkbox Combined --
    result_checkbox_1 = fields.Boolean(
        string='Checkbox 1',
        default=False
    )

    result_checkbox_2 = fields.Boolean(
        string='Checkbox 2',
        default=False
    )

    checkbox_result_confirmed = fields.Boolean(
        string='Resultado Checkbox Confirmado',
        default=False,
        help='Se activa cuando el usuario interactúa con los checkboxes'
    )

    # -- Conditional Numeric Range --
    available_conditional_option_ids = fields.Many2many(
        'amunet.quality.parameter.conditional.option',
        compute='_compute_available_conditional_options',
        string='Opciones disponibles',
        help='Opciones condicionales disponibles para esta especificación'
    )

    result_conditional_option_id = fields.Many2one(
        'amunet.quality.parameter.conditional.option',
        string='Opción seleccionada',
        help='Opción condicional seleccionada (ej: 5 µL, 100 µL)',
        domain="[('id', 'in', available_conditional_option_ids)]"
    )

    result_conditional_value = fields.Float(
        string='Valor medido (condicional)',
        digits='Product Unit of Measure',
        help='Valor numérico medido para la opción seleccionada'
    )
    
    result_conditional_value_filled = fields.Boolean(
        string='Campo condicional llenado',
        default=False,
        help='Indica si el usuario ya ingresó un valor en result_conditional_value'
    )

    # -- Text Pattern --
    result_text_pattern = fields.Char(
        string='Patrón ingresado',
        help='Patrón de texto ingresado por el analista (ej: AAAAA)'
    )

    constructed_phrase = fields.Text(
        string='Frase construida',
        compute='_compute_constructed_phrase',
        store=True,
        help='Frase descriptiva construida desde el patrón'
    )

    failed_positions = fields.Char(
        string='Posiciones fallidas',
        compute='_compute_verdict',
        store=True,
        help='Posiciones del patrón que no cumplen'
    )

    # -- Expected vs Obtained --
    result_expected_type = fields.Char(
        string='Tipo esperado',
        help='Tipo de muestra esperado (ej: Positivo, Negativo)'
    )

    result_obtained_type = fields.Char(
        string='Resultado obtenido',
        help='Resultado obtenido (ej: Positivo, Negativo)'
    )

    # -- Binary with Notes --
    result_binary_option = fields.Selection([
        ('pass', 'Cumple'),
        ('fail', 'No Cumple'),
    ], string='Resultado (binary con notas)')

    result_notes = fields.Text(
        string='Notas obligatorias',
        help='Notas obligatorias cuando no cumple'
    )

    # -- Ternary with N/A --
    result_ternary = fields.Selection([
        ('yes', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A'),
    ], string='Resultado (ternario)')

    # -- Decision Matrix (MAVI-16) --
    result_dm_step1_concentration = fields.Selection([
        ('low', 'Baja'),
        ('medium', 'Intermedia'),
        ('high', 'Alta'),
    ], string='1️⃣ Concentración objetivo',
        help='Paso 1: Seleccione la concentración objetivo para la evaluación')

    result_dm_step2_1_control_visible = fields.Selection([
        ('yes', 'Sí, visible'),
        ('no', 'No visible'),
    ], string='2️⃣ Línea C Visible',
        help='Paso 2.1: ¿La línea de control (C) es visible? Si NO, la prueba es inválida.')

    result_dm_step2_2_comparison = fields.Selection([
        ('t_neq_r', 'T ≠ R (No hay línea T)'),
        ('t_lt_r', 'T < R (Menor intensidad)'),
        ('t_eq_r', 'T ~ R (Intensidad similar)'),
        ('t_gt_r', 'T > R (Mayor intensidad)'),
    ], string='3️⃣ Comparación T vs R',
        help='Paso 2.2: Compare visualmente la región de prueba (T) con la de referencia (R)')

    # -- MAVI-07 --
    mavi07_sample_type = fields.Selection([
        ('negative', 'Muestra Negativa'),
        ('positive', 'Muestra Positiva')
    ], string='Tipo de Muestra')

    mavi07_observed_result = fields.Selection([
        ('result_1', '#1'),
        ('result_2', '#2'),
        ('result_3', '#3'),
        ('result_4', '#4'),
        ('result_5', '#5')
    ], string='Resultado Observado')

    mavi07_expected_result = fields.Char(
        string='Resultado Esperado',
        compute='_compute_mavi07_expected',
        store=True
    )

    # -- VAMA-034 --
    vama034_sample_type = fields.Selection([
        ('negative', 'Opción A: Negativa'),
        ('positive', 'Opción B: Positiva'),
    ], string="Tipo de Muestra")

    vama034_observed_result = fields.Selection([
        ('control_only', 'Opción A: Visualización sólo de la línea control.'),
        ('control_test', 'Opción B: Visualización de línea control y línea de prueba.'),
    ], string="Resultado Observado")

    # -- VAMA-006: Escala de Color NPS --
    vama006_color_value = fields.Integer(
        string='Tonalidad Observada (0-14)',
        default=-1,  # -1 means nothing selected
    )

    # -- VAMA-067: Tolerancia a la Centrifugación --
    vama067_particles = fields.Selection([
        ('no_particles', 'Opción A: Sin partículas oscuras visibles.'),
        ('with_particles', 'Opción B: Con partículas oscuras visibles.'),
    ], string='Paso 1: Presencia de Partículas')

    vama067_color = fields.Selection([
        ('similar_color', 'Opción A: Color similar.'),
        ('different_color', 'Opción B: Color distinto.'),
    ], string='Paso 2: Color de la Solución')

    # -- MAVI-15 --
    mavi15_result = fields.Selection([
        ('opcion_a', 'Opción A: Si coincide.'),
        ('opcion_b', 'Opción B: No coincide.'),
        ('opcion_c', 'Opción C: Sin visualización de la línea control pese a la coincidencia con el patrón colorimétrico.'),
    ], string='Selección MAVI-15')

    # -- MAVI-07 HM --
    mavi07_hm_sample_type = fields.Selection([
        ('negative', 'Negativa'),
        ('positive', 'Positiva'),
    ], string='MAVI-07 HM: Tipo Muestra')
    mavi07_hm_result = fields.Selection([
        ('pass', 'Pasa'),
        ('fail', 'Falla'),
    ], string='MAVI-07 HM: Resultado')

    # -- MAVI-11 --
    mavi11_target_height = fields.Char(string='MAVI-11: Altura Objetivo')
    mavi11_measured_height = fields.Float(string='MAVI-11: Altura Medida')

    # -- MGA-0981 --
    mga0981_vol_declarado = fields.Char(string='MGA-0981: Vol. Declarado')
    mga0981_vol_obtenido = fields.Float(string='MGA-0981: Vol. Obtenido')

    # -- VAMA-105 --
    vama105_nominal_volume = fields.Char(string='VAMA-105: Vol. Nominal')
    vama105_measured_volume = fields.Float(string='VAMA-105: Vol. Medido')

    # -- VAMA-112 --
    vama112_cond1 = fields.Selection([('adequate', 'Adecuado'), ('inadequate', 'No adecuado')], string='VAMA-112: Cond1')
    vama112_cond2 = fields.Selection([('no_abrupt', 'Sin movimientos bruscos'), ('abrupt', 'Con movimientos bruscos')], string='VAMA-112: Cond2')
    vama112_cond3 = fields.Selection([('correct', 'Correcta'), ('incorrect', 'Incorrecta')], string='VAMA-112: Cond3')
    vama112_cond4 = fields.Selection([('complete', 'Completa'), ('incomplete', 'Incompleta')], string='VAMA-112: Cond4')
    vama112_cond5 = fields.Selection([('no_heat', 'Sin calentar'), ('heating', 'Calentando')], string='VAMA-112: Cond5')


    # -- Multi-Check --
    multi_check_results_json = fields.Text(string='Resultados Multi-Check (JSON)')

    # -- Multi-Condición Numérica (VAMA-096) --
    multi_cond_binary = fields.Selection([
        ('correct', 'Funcionamiento Correcto'),
        ('incorrect', 'Funcionamiento Incorrecto')
    ], string='Funcionamiento del Vial')

    multi_cond_num1 = fields.Integer(string='Número de Gotas')
    multi_cond_num1_filled = fields.Boolean(string='Num1 llenado', compute='_compute_multi_cond_filled', store=True)
    multi_cond_num1_min = fields.Integer(string='Mínimo Gotas', default=5)

    multi_cond_num2 = fields.Float(string='Volumen de Gota (µl)', digits=(10, 2))
    multi_cond_num2_filled = fields.Boolean(string='Num2 llenado', compute='_compute_multi_cond_filled', store=True)
    multi_cond_num2_min = fields.Float(string='Volumen Mínimo', default=40.0)
    multi_cond_num2_max = fields.Float(string='Volumen Máximo', default=50.0)

    multi_cond_result_text = fields.Text(
        string='Resultado Generado',
        compute='_compute_multi_cond_result',
        store=True
    )

    # -- VAMA-044: Funcionalidad de Tubo (4 condiciones) --
    vama044_num_gotas = fields.Integer(string='Número de Gotas')
    vama044_num_gotas_filled = fields.Boolean(string='NumGotas llenado', default=False)
    vama044_num_gotas_min = fields.Integer(string='Mínimo Gotas', default=5)
    
    vama044_vol_gota = fields.Float(string='Volumen de Gota (µl)', digits=(10, 2))
    vama044_vol_gota_filled = fields.Boolean(string='VolGota llenado', default=False)
    vama044_vol_gota_min = fields.Float(string='Vol Gota Mín', default=40.0)
    vama044_vol_gota_max = fields.Float(string='Vol Gota Máx', default=50.0)
    
    vama044_union = fields.Selection([
        ('adequate', 'Unión adecuada'),
        ('inadequate', 'Unión inadecuada')
    ], string='Unión Tapa-Tubo')
    
    vama044_vol_llenado = fields.Float(string='Volumen de Llenado (µl)', digits=(10, 2))
    vama044_vol_llenado_filled = fields.Boolean(string='VolLlenado llenado', default=False)
    vama044_vol_llenado_min = fields.Float(string='Vol Llenado Mín', default=1540.0)
    vama044_vol_llenado_max = fields.Float(string='Vol Llenado Máx', default=1560.0)
    
    vama044_result_text = fields.Text(
        string='Resultado Generado VAMA-044',
        compute='_compute_vama044_result',
        store=True
    )

    # -- VAMA-112: Multi-Checkbox Centrífuga --
    vama112_cond1 = fields.Selection([
        ('adequate', 'Adecuado'),
        ('inadequate', 'No adecuado')
    ], string='Funcionamiento General')
    
    vama112_cond2 = fields.Selection([
        ('no_abrupt', 'Sin movimientos bruscos'),
        ('abrupt', 'Con movimientos bruscos')
    ], string='Movimientos')
    
    vama112_cond3 = fields.Selection([
        ('correct', 'Correcta'),
        ('incorrect', 'Incorrecta')
    ], string='Separación Correcta')
    
    vama112_cond4 = fields.Selection([
        ('complete', 'Completa'),
        ('incomplete', 'Incompleta')
    ], string='Separación Completa')
    
    vama112_cond5 = fields.Selection([
        ('no_heat', 'Sin calentar'),
        ('heating', 'Calentando')
    ], string='Temperatura')
    
    vama112_result_text = fields.Text(
        string='Resultado Generado VAMA-112',
        compute='_compute_vama112_result',
        store=True
    )

    # -- VAMA-078: Multi-Visual Liofilizado --
    vama078_color = fields.Selection([
        ('yellow', 'Amarillo'),
        ('white', 'Blanco')
    ], string='Color del Liofilizado')
    
    vama078_forma = fields.Selection([
        ('deformed', 'Deformado'),
        ('compact', 'Compacto')
    ], string='Forma del Liofilizado')
    
    vama078_textura = fields.Selection([
        ('no_sticky', 'Sin textura pegajosa'),
        ('sticky', 'Con textura pegajosa')
    ], string='Textura del Liofilizado')
    
    vama078_humedad = fields.Selection([
        ('no_moisture', 'Sin humedad aparente'),
        ('moisture', 'Con humedad aparente')
    ], string='Humedad Aparente')
    
    vama078_result_text = fields.Text(
        string='Resultado Generado VAMA-078',
        compute='_compute_vama078_result',
        store=True
    )


    # Campos computados para matriz de decisión
    dm_matched_scenario_id = fields.Many2one(
        'amunet.quality.parameter.decision.matrix',
        string='Escenario Encontrado',
        compute='_compute_verdict',
        store=True,
        help='El escenario de la matriz que coincide con las selecciones'
    )

    dm_step2_2_unlocked = fields.Boolean(
        string='Paso 2.2 Desbloqueado',
        compute='_compute_dm_step_states',
        help='Indica si el paso 2.2 está disponible (cuando línea C es visible)'
    )

    dm_step2_1_unlocked = fields.Boolean(
        string='Paso 2.1 Desbloqueado',
        compute='_compute_dm_step_states',
        help='Indica si el paso 2.1 está disponible (cuando paso 1 tiene valor)'
    )

    dm_current_step = fields.Integer(
        string='Paso Actual',
        compute='_compute_dm_step_states',
        help='Número del paso actual en el flujo (1, 2 o 3)'
    )

    # ========== Configuración de Evaluación (copiados de config) ==========

    # -- Numeric Range --
    min_value = fields.Float(
        string='Mínimo',
        digits='Product Unit of Measure'
    )

    max_value = fields.Float(
        string='Máximo',
        digits='Product Unit of Measure'
    )

    uom_id = fields.Many2one(
        'uom.uom',
        string='Unidad de Medida'
    )

    # -- Binary Selection --
    expected_value_binary = fields.Char(
        string='Valor Esperado (Binary)'
    )

    binary_option_pass = fields.Char(
        string='Opción Cumple'
    )

    binary_option_fail = fields.Char(
        string='Opción No Cumple'
    )

    # -- Checkbox Combined --
    checkbox_label_1 = fields.Char(
        string='Etiqueta Checkbox 1'
    )

    checkbox_label_2 = fields.Char(
        string='Etiqueta Checkbox 2'
    )

    # -- Text Pattern --
    text_pattern_expected = fields.Char(
        string='Patrón Esperado'
    )

    text_pattern_regex = fields.Char(
        string='Expresión Regular'
    )

    text_phrase_mapping = fields.Text(
        string='Mapeo de Frases (JSON)'
    )
    
    # Campo related para traer el mapping desde la configuración (sin store=True para evitar columna en BD)
    config_text_phrase_mapping = fields.Text(
        string='Mapeo desde Configuración',
        related='specification_config_id.text_phrase_mapping',
        readonly=True
    )

    # -- Expected vs Obtained --
    expected_options = fields.Char(
        string='Opciones Esperadas'
    )

    obtained_options = fields.Char(
        string='Opciones Obtenidas'
    )

    # -- Binary with Notes --
    binary_notes_option_pass = fields.Char(
        string='Opción Cumple (Notas)'
    )

    binary_notes_option_fail = fields.Char(
        string='Opción No Cumple (Notas)'
    )

    # -- Ternary with N/A --
    ternary_option_yes = fields.Char(
        string='Opción Sí',
        default='Sí'
    )

    ternary_option_no = fields.Char(
        string='Opción No',
        default='No'
    )

    ternary_option_na = fields.Char(
        string='Opción N/A',
        default='N/A'
    )

    # -- Decision Matrix (MAVI-16) Config --
    dm_step1_label = fields.Char(
        string='Etiqueta Paso 1',
        default='Concentración objetivo'
    )

    dm_step2_1_label = fields.Char(
        string='Etiqueta Paso 2.1',
        default='Línea de control (C) visible'
    )

    dm_step2_2_label = fields.Char(
        string='Etiqueta Paso 2.2',
        default='Comparación visual T vs R'
    )

    # ========== Dictamen ==========

    verdict = fields.Selection([
        ('pending', 'Pendiente'),
        ('pass', 'Cumple'),
        ('fail', 'No Cumple'),
        ('not_applicable', 'No Aplica'),
    ], string='Dictamen', compute='_compute_verdict', store=True,
        help='Resultado de la evaluación')

    verdict_display = fields.Char(
        string='Dictamen (Display)',
        compute='_compute_verdict_display'
    )

    verdict_message = fields.Text(
        string='Mensaje de Dictamen',
        compute='_compute_verdict',
        store=True
    )

    result_display = fields.Char(
        string='Resultado (Display)',
        compute='_compute_result_display'
    )

    # ========== Campos Computados Específicos ==========

    @api.depends('evaluation_type', 'mavi07_sample_type')
    def _compute_mavi07_expected(self):
        for record in self:
            if record.evaluation_type != 'mavi_07':
                record.mavi07_expected_result = False
                continue

            if record.mavi07_sample_type == 'negative':
                record.mavi07_expected_result = '#5'
            elif record.mavi07_sample_type == 'positive':
                record.mavi07_expected_result = '#1, #2, #3 o #4'
            else:
                record.mavi07_expected_result = False

    @api.depends('multi_cond_num1', 'multi_cond_num2')
    def _compute_multi_cond_filled(self):
        """Compute if multi_cond fields have been filled"""
        for record in self:
            record.multi_cond_num1_filled = bool(record.multi_cond_num1 or record.multi_cond_num1 == 0)
            record.multi_cond_num2_filled = bool(record.multi_cond_num2 or record.multi_cond_num2 == 0.0)

    @api.depends('evaluation_type', 'multi_cond_binary', 'multi_cond_num1', 'multi_cond_num2')
    def _compute_multi_cond_result(self):
        for record in self:
            if record.evaluation_type != 'multi_condition_numeric':
                record.multi_cond_result_text = False
                continue

            if not all([record.multi_cond_binary, record.multi_cond_num1, record.multi_cond_num2]):
                record.multi_cond_result_text = False
                continue

            func_text = 'correcto' if record.multi_cond_binary == 'correct' else 'incorrecto'
            record.multi_cond_result_text = (
                f"Funcionamiento {func_text} del vial, "
                f"obtención de {record.multi_cond_num1} gotas, "
                f"con un volumen de gota de {record.multi_cond_num2} µl."
            )

    @api.depends('evaluation_type', 'vama044_num_gotas', 'vama044_vol_gota', 'vama044_union', 'vama044_vol_llenado')
    def _compute_vama044_result(self):
        """Genera texto de resultado para VAMA-044"""
        for record in self:
            if record.evaluation_type != 'vama_044':
                record.vama044_result_text = False
                continue
            
            if not all([
                record.vama044_num_gotas,
                record.vama044_vol_gota,
                record.vama044_union,
                record.vama044_vol_llenado
            ]):
                record.vama044_result_text = False
                continue
            
            union_text = 'adecuada' if record.vama044_union == 'adequate' else 'inadecuada'
            record.vama044_result_text = (
                f"Obtención de {record.vama044_num_gotas} gotas, "
                f"con un volumen de gota de {record.vama044_vol_gota} µl, "
                f"unión {union_text} de la tapa cuentagotas y tubo colector, "
                f"con volumen de llenado de {record.vama044_vol_llenado} µl."
            )

    @api.depends('evaluation_type', 'vama112_cond1', 'vama112_cond2', 'vama112_cond3', 'vama112_cond4', 'vama112_cond5')
    def _compute_vama112_result(self):
        """Genera texto de resultado para VAMA-112"""
        for record in self:
            if record.evaluation_type != 'vama_112':
                record.vama112_result_text = False
                continue
            
            if not all([record.vama112_cond1, record.vama112_cond2, record.vama112_cond3,
                        record.vama112_cond4, record.vama112_cond5]):
                record.vama112_result_text = False
                continue
            
            func_text = 'adecuado' if record.vama112_cond1 == 'adequate' else 'no adecuado'
            mov_text = 'sin movimientos bruscos' if record.vama112_cond2 == 'no_abrupt' else 'con movimientos bruscos'
            sep_corr = 'correcta' if record.vama112_cond3 == 'correct' else 'incorrecta'
            sep_comp = 'completa' if record.vama112_cond4 == 'complete' else 'incompleta'
            temp_text = 'sin calentar' if record.vama112_cond5 == 'no_heat' else 'calentando'
            
            record.vama112_result_text = (
                f"Funcionamiento general {func_text}, "
                f"{mov_text}, "
                f"separación {sep_corr} y {sep_comp}, "
                f"{temp_text}."
            )

    @api.depends('evaluation_type', 'vama078_color', 'vama078_forma', 'vama078_textura', 'vama078_humedad')
    def _compute_vama078_result(self):
        """Genera texto de resultado para VAMA-078"""
        for record in self:
            if record.evaluation_type != 'vama_078':
                record.vama078_result_text = False
                continue
            
            if not all([record.vama078_color, record.vama078_forma,
                        record.vama078_textura, record.vama078_humedad]):
                record.vama078_result_text = False
                continue
            
            color_text = 'amarillo' if record.vama078_color == 'yellow' else 'blanco'
            forma_text = 'deformado' if record.vama078_forma == 'deformed' else 'compacto'
            textura_text = 'sin textura pegajosa' if record.vama078_textura == 'no_sticky' else 'con textura pegajosa'
            humedad_text = 'sin humedad aparente' if record.vama078_humedad == 'no_moisture' else 'con humedad aparente'
            
            record.vama078_result_text = (
                f"Liofilizado {color_text} y {forma_text}, "
                f"{textura_text} y {humedad_text}."
            )


    # ========== Campos Computados ==========

    @api.depends('result_text_pattern', 'text_phrase_mapping', 'text_pattern_expected')
    def _compute_constructed_phrase(self):
        """Construye la frase descriptiva desde el patrón ingresado"""
        for record in self:
            if record.evaluation_type == 'text_pattern' and record.result_text_pattern:
                record.constructed_phrase = record._build_phrase_from_pattern()
            else:
                record.constructed_phrase = ''

    # ========== Métodos onchange para rastrear si campos fueron llenados ==========
    
    @api.onchange('result_numeric')
    def _onchange_result_numeric(self):
        """Marca el campo como llenado cuando el usuario ingresa un valor"""
        if self.result_numeric or self.result_numeric == 0:
            self.result_numeric_filled = True
    
    @api.onchange('result_conditional_value')
    def _onchange_result_conditional_value(self):
        """Marca el campo como llenado cuando el usuario ingresa un valor"""
        if self.result_conditional_value or self.result_conditional_value == 0:
            self.result_conditional_value_filled = True
    
    @api.onchange('multi_cond_num1')
    def _onchange_multi_cond_num1(self):
        """Marca el campo como llenado cuando el usuario ingresa un valor"""
        if self.multi_cond_num1 or self.multi_cond_num1 == 0:
            self.multi_cond_num1_filled = True
    
    @api.onchange('multi_cond_num2')
    def _onchange_multi_cond_num2(self):
        """Marca el campo como llenado cuando el usuario ingresa un valor"""
        if self.multi_cond_num2 or self.multi_cond_num2 == 0:
            self.multi_cond_num2_filled = True
    
    @api.onchange('vama044_num_gotas')
    def _onchange_vama044_num_gotas(self):
        """Marca el campo como llenado cuando el usuario ingresa un valor"""
        if self.vama044_num_gotas or self.vama044_num_gotas == 0:
            self.vama044_num_gotas_filled = True
    
    @api.onchange('vama044_vol_gota')
    def _onchange_vama044_vol_gota(self):
        """Marca el campo como llenado cuando el usuario ingresa un valor"""
        if self.vama044_vol_gota or self.vama044_vol_gota == 0:
            self.vama044_vol_gota_filled = True
    
    @api.onchange('vama044_vol_llenado')
    def _onchange_vama044_vol_llenado(self):
        """Marca el campo como llenado cuando el usuario ingresa un valor"""
        if self.vama044_vol_llenado or self.vama044_vol_llenado == 0:
            self.vama044_vol_llenado_filled = True

    def _build_phrase_from_pattern(self):
        """Construye la frase descriptiva desde el patrón"""
        self.ensure_one()
        
        pattern_input = (self.result_text_pattern or '').upper()
        
        if not pattern_input or not self.text_phrase_mapping:
            return pattern_input

        try:
            mapping = json.loads(self.text_phrase_mapping)
            positions = mapping.get('positions', [])
            phrase_template = mapping.get('phrase_template', '')

            if phrase_template:
                values = {}
                for pos in positions:
                    idx = pos.get('index', 0)
                    if idx < len(pattern_input):
                        char = pattern_input[idx]
                        values[str(idx)] = pos.get(char, char)

                result = phrase_template
                for key, value in values.items():
                    result = result.replace(f'{{{key}}}', value)
                return result
            else:
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

    @api.depends('result_dm_step1_concentration', 'result_dm_step2_1_control_visible')
    def _compute_dm_step_states(self):
        """Calcula el estado de desbloqueo de los pasos de la matriz de decisión"""
        for record in self:
            if record.evaluation_type != 'decision_matrix':
                record.dm_step2_1_unlocked = False
                record.dm_step2_2_unlocked = False
                record.dm_current_step = 0
                continue

            # Paso 1 siempre disponible
            # Paso 2.1 se desbloquea cuando hay valor en paso 1
            record.dm_step2_1_unlocked = bool(record.result_dm_step1_concentration)

            # Paso 2.2 se desbloquea cuando línea C es visible
            # Si línea C NO es visible, el paso 2.2 permanece bloqueado
            record.dm_step2_2_unlocked = (
                record.result_dm_step2_1_control_visible == 'yes'
            )

            # Determinar paso actual
            if not record.result_dm_step1_concentration:
                record.dm_current_step = 1
            elif not record.result_dm_step2_1_control_visible:
                record.dm_current_step = 2
            elif record.result_dm_step2_1_control_visible == 'no':
                # Fallo inmediato - no hay paso siguiente
                record.dm_current_step = 2
            elif not record.result_dm_step2_2_comparison:
                record.dm_current_step = 3
            else:
                record.dm_current_step = 0  # Completado

    @api.depends(
        'evaluation_type', 'result_selection', 'result_numeric', 'result_checkbox_1',
        'result_checkbox_2', 'checkbox_result_confirmed', 'result_conditional_option_id',
        'result_conditional_value', 'result_text_pattern', 'text_pattern_expected',
        'text_pattern_regex', 'result_expected_type', 'result_obtained_type',
        'result_binary_option', 'result_notes', 'result_ternary',
        'result_dm_step1_concentration', 'result_dm_step2_1_control_visible',
        'result_dm_step2_2_comparison', 'specification_config_id',
        'min_value', 'max_value', 'expected_value_binary',
        'binary_option_pass', 'binary_option_fail',
        'checkbox_label_1', 'checkbox_label_2',
        'mavi07_sample_type', 'mavi07_observed_result',
        'vama034_sample_type', 'vama034_observed_result',
        'vama006_color_value',
        'vama067_particles', 'vama067_color',
        'multi_cond_binary', 'multi_cond_num1', 'multi_cond_num2',
        'multi_cond_num1_filled', 'multi_cond_num2_filled',
        'vama044_num_gotas', 'vama044_vol_gota', 'vama044_union', 'vama044_vol_llenado',
        'vama112_cond1', 'vama112_cond2', 'vama112_cond3', 'vama112_cond4', 'vama112_cond5',
        'vama078_color', 'vama078_forma', 'vama078_textura', 'vama078_humedad',
        'vama105_nominal_volume', 'vama105_measured_volume',
        'mga0981_vol_declarado', 'mga0981_vol_obtenido',
        'mavi15_result'
    )
    def _compute_verdict(self):
        """Evalúa el resultado y determina el dictamen"""
        for record in self:
            result = record._evaluate_result()
            record.verdict = result.get('verdict', 'pending')
            record.verdict_message = result.get('message', '')
            record.failed_positions = result.get('failed_positions', '')
            # Para decision_matrix, también almacenamos el escenario encontrado
            record.dm_matched_scenario_id = result.get('scenario_id', False)

    def _evaluate_result(self):
        """Evalúa el resultado según el tipo de evaluación"""
        self.ensure_one()

        if self.evaluation_type == 'binary_selection':
            return self._evaluate_binary_selection()
        elif self.evaluation_type == 'numeric_range':
            return self._evaluate_numeric_range()
        elif self.evaluation_type == 'checkbox_combined':
            return self._evaluate_checkbox_combined()
        elif self.evaluation_type == 'conditional_numeric_range':
            return self._evaluate_conditional_numeric_range()
        elif self.evaluation_type == 'text_pattern':
            return self._evaluate_text_pattern()
        elif self.evaluation_type == 'expected_vs_obtained':
            return self._evaluate_expected_vs_obtained()
        elif self.evaluation_type == 'binary_with_notes':
            return self._evaluate_binary_with_notes()
        elif self.evaluation_type == 'ternary_with_na':
            return self._evaluate_ternary_with_na()
        elif self.evaluation_type == 'decision_matrix':
            return self._evaluate_decision_matrix()
        elif self.evaluation_type == 'mavi_07':
            return self._evaluate_mavi_07()
        elif self.evaluation_type == 'vama_034':
            return self._evaluate_vama_034()
        elif self.evaluation_type == 'vama_006':
            return self._evaluate_vama_006()
        elif self.evaluation_type == 'vama_067':
            return self._evaluate_vama_067()
        elif self.evaluation_type == 'multi_condition_numeric':
            return self._evaluate_multi_condition_numeric()
        elif self.evaluation_type == 'vama_044':
            return self._evaluate_vama_044()
        elif self.evaluation_type == 'vama_112':
            return self._evaluate_vama_112()
        elif self.evaluation_type == 'vama_078':
            return self._evaluate_vama_078()
        elif self.evaluation_type == 'vama_105':
            return self._evaluate_vama_105()
        elif self.evaluation_type == 'mga_0981':
            return self._evaluate_mga_0981()
        elif self.evaluation_type == 'mavi_11_height':
            return self._evaluate_mavi_11_height()
        elif self.evaluation_type == 'mavi_15_ternary':
            return self._evaluate_mavi_15_ternary()
        elif self.evaluation_type in ('vama_multi_check', 'mavi_07_ternary', 'mavi_07'):
            return self._evaluate_vama_multi_check()
        else:
            return {'verdict': 'pending', 'message': 'Tipo de evaluación no implementado'}

    def _evaluate_binary_selection(self):
        """Evalúa selección binaria"""
        if not self.result_selection:
            return {'verdict': 'pending', 'message': 'Seleccione una opción'}

        if self.result_selection == self.binary_option_pass:
            return {'verdict': 'pass', 'message': self.result_selection}
        else:
            return {'verdict': 'fail', 'message': self.result_selection}

    def action_select_pass(self):
        """Selecciona la opción que cumple"""
        self.ensure_one()
        self.result_selection = self.binary_option_pass
        return True

    def action_select_fail(self):
        """Selecciona la opción que no cumple"""
        self.ensure_one()
        self.result_selection = self.binary_option_fail
        return True

    def _evaluate_numeric_range(self):
        """Evalúa rango numérico"""
        # Verificar si el usuario ha llenado el campo
        if not self.result_numeric_filled:
            return {'verdict': 'pending', 'message': 'Ingrese un valor numérico'}
        
        # Si llegamos aquí, el usuario ha ingresado un valor (puede ser 0, que es válido)
        value = self.result_numeric
        uom_name = self.uom_id.name if self.uom_id else ''

        if self.min_value <= value <= self.max_value:
            return {
                'verdict': 'pass',
                'message': f'{value} {uom_name} (rango: {self.min_value}-{self.max_value})'
            }
        else:
            return {
                'verdict': 'fail',
                'message': f'{value} {uom_name} fuera de rango ({self.min_value}-{self.max_value})'
            }

    def _evaluate_checkbox_combined(self):
        """Evalúa checkboxes combinados"""
        cb1 = self.result_checkbox_1
        cb2 = self.result_checkbox_2

        # Si no se ha confirmado la interacción del usuario, está pendiente
        if not self.checkbox_result_confirmed:
            return {'verdict': 'pending', 'message': 'Marque los checkboxes aplicables'}

        # Asumimos que se requieren ambos (configurable en especificación)
        if cb1 and cb2:
            return {
                'verdict': 'pass',
                'message': f'✓ {self.checkbox_label_1}, ✓ {self.checkbox_label_2}'
            }
        else:
            parts = []
            parts.append(f'{"✓" if cb1 else "✗"} {self.checkbox_label_1}')
            parts.append(f'{"✓" if cb2 else "✗"} {self.checkbox_label_2}')
            return {'verdict': 'fail', 'message': ', '.join(parts)}

    def _evaluate_conditional_numeric_range(self):
        """Evalúa rango numérico condicional"""
        if not self.result_conditional_option_id:
            return {'verdict': 'pending', 'message': 'Seleccione una opción'}

        option = self.result_conditional_option_id

        # Si la opción es N/A, no se requiere valor numérico
        if option.is_not_applicable:
            return {'verdict': 'not_applicable', 'message': f'{option.name} - Excluida del conteo'}

        # Verificar si el usuario ha llenado el campo de valor
        if not self.result_conditional_value_filled:
            return {'verdict': 'pending', 'message': 'Ingrese el valor medido'}

        value = self.result_conditional_value
        uom_name = option.uom_id.name if option.uom_id else ''

        if option.min_value <= value <= option.max_value:
            return {
                'verdict': 'pass',
                'message': f'{value} {uom_name} ({option.name}: {option.min_value}-{option.max_value})'
            }
        else:
            return {
                'verdict': 'fail',
                'message': f'{value} {uom_name} fuera de rango ({option.name}: {option.min_value}-{option.max_value})'
            }

    def _evaluate_text_pattern(self):
        """Evalúa texto con patrón (VAMA-112)"""
        pattern_input = (self.result_text_pattern or '').upper()

        if not pattern_input:
            return {'verdict': 'pending', 'message': 'Ingrese el patrón'}

        # Validar formato con regex
        if self.text_pattern_regex:
            if not re.match(self.text_pattern_regex, pattern_input):
                expected_len = len(self.text_pattern_expected or '')
                return {
                    'verdict': 'fail',
                    'message': f'Formato inválido. Use solo caracteres permitidos, longitud {expected_len}'
                }

        # Validar longitud
        expected_len = len(self.text_pattern_expected or '')
        if len(pattern_input) != expected_len:
            return {
                'verdict': 'fail',
                'message': f'Longitud incorrecta. Esperado: {expected_len}, Ingresado: {len(pattern_input)}'
            }

        # Construir frase
        phrase = self._build_phrase_from_pattern()

        # Comparar con patrón esperado
        if pattern_input == (self.text_pattern_expected or '').upper():
            return {
                'verdict': 'pass',
                'message': phrase,
                'constructed_phrase': phrase
            }
        else:
            # Identificar posiciones fallidas
            failed = []
            expected = (self.text_pattern_expected or '').upper()
            for i, (inp, exp) in enumerate(zip(pattern_input, expected)):
                if inp != exp:
                    failed.append(str(i + 1))
            failed_str = ', '.join(failed) if failed else 'Ninguna'

            return {
                'verdict': 'fail',
                'message': f'{phrase}\n\nPosiciones que no cumplen: {failed_str}',
                'constructed_phrase': phrase,
                'failed_positions': failed_str
            }

    def _evaluate_expected_vs_obtained(self):
        """Evalúa comparación esperado vs obtenido (VAMA-032)"""
        if not self.result_expected_type:
            return {'verdict': 'pending', 'message': 'Seleccione el tipo de muestra'}

        if not self.result_obtained_type:
            return {'verdict': 'pending', 'message': 'Seleccione el resultado obtenido'}

        expected = self.result_expected_type.strip()
        obtained = self.result_obtained_type.strip()

        if expected == obtained:
            return {
                'verdict': 'pass',
                'message': f'Muestra {expected}: {obtained} ✓'
            }
        else:
            return {
                'verdict': 'fail',
                'message': f'El resultado ({obtained}) no coincide con el tipo de muestra ({expected})'
            }

    def _evaluate_binary_with_notes(self):
        """Evalúa binary con notas (VAMA-063)"""
        if not self.result_binary_option:
            return {'verdict': 'pending', 'message': 'Seleccione una opción'}

        if self.result_binary_option == 'pass':
            return {
                'verdict': 'pass',
                'message': self.binary_notes_option_pass or 'Cumple'
            }
        else:
            notes = (self.result_notes or '').strip()
            message = self.binary_notes_option_fail or 'No cumple'
            if notes:
                message += f'. Nota: {notes}'
            elif not notes:
                # Las notas pueden ser requeridas pero permitimos pending para que el usuario las complete
                message += ' (pendiente: agregar notas)'

            return {'verdict': 'fail', 'message': message}

    def _evaluate_ternary_with_na(self):
        """Evalúa ternario con N/A (MAVI-14)"""
        if not self.result_ternary:
            return {'verdict': 'pending', 'message': 'Seleccione una opción'}

        if self.result_ternary == 'yes':
            return {'verdict': 'pass', 'message': self.ternary_option_yes or 'Sí'}
        elif self.result_ternary == 'no':
            return {'verdict': 'fail', 'message': self.ternary_option_no or 'No'}
        elif self.result_ternary == 'na':
            return {'verdict': 'not_applicable', 'message': f'{self.ternary_option_na or "N/A"} - Excluida del conteo'}

        return {'verdict': 'pending', 'message': 'Opción no reconocida'}

    def _evaluate_decision_matrix(self):
        """
        Evalúa matriz de decisión multi-paso (MAVI-16).
        
        Flujo de evaluación:
        1. Paso 1: Seleccionar concentración objetivo (Baja/Intermedia/Alta)
        2. Paso 2.1: ¿Línea de control (C) visible? (Sí/No)
           - Si NO: Fallo inmediato, prueba inválida
        3. Paso 2.2: Comparación visual T vs R (T≠R, T<R, T~R, T>R)
        
        La evaluación busca el escenario coincidente en la matriz de decisión
        configurada en la especificación.
        
        Returns:
            dict: {'verdict': str, 'message': str, 'scenario_id': int or False}
        """
        # Validar Paso 1: Concentración objetivo
        if not self.result_dm_step1_concentration:
            return {
                'verdict': 'pending',
                'message': '1️⃣ Seleccione la concentración objetivo',
                'scenario_id': False
            }

        # Validar Paso 2.1: Línea de control visible
        if not self.result_dm_step2_1_control_visible:
            return {
                'verdict': 'pending',
                'message': '2️⃣ Indique si la línea de control (C) es visible',
                'scenario_id': False
            }

        # Si línea C NO es visible: Fallo inmediato (Escenario 1)
        if self.result_dm_step2_1_control_visible == 'no':
            # Buscar escenario de fallo por línea C no visible
            scenario = self._find_decision_matrix_scenario(
                concentration=self.result_dm_step1_concentration,
                control_visible=False,
                comparison=None
            )
            if scenario:
                return {
                    'verdict': scenario.verdict,
                    'message': scenario.result_message,
                    'scenario_id': scenario.id
                }
            # Fallback si no hay escenario configurado
            return {
                'verdict': 'fail',
                'message': 'Inválido: No hay visualización de la línea de control.',
                'scenario_id': False
            }

        # Línea C visible: Validar Paso 2.2: Comparación T vs R
        if not self.result_dm_step2_2_comparison:
            return {
                'verdict': 'pending',
                'message': '3️⃣ Compare visualmente T vs R',
                'scenario_id': False
            }

        # Buscar escenario en la matriz de decisión
        scenario = self._find_decision_matrix_scenario(
            concentration=self.result_dm_step1_concentration,
            control_visible=True,
            comparison=self.result_dm_step2_2_comparison
        )

        if scenario:
            return {
                'verdict': scenario.verdict,
                'message': scenario.result_message,
                'scenario_id': scenario.id
            }

        # Fallback si no se encuentra escenario
        concentration_labels = {
            'low': 'Baja',
            'medium': 'Intermedia',
            'high': 'Alta',
        }
        comparison_labels = {
            't_neq_r': 'T ≠ R',
            't_lt_r': 'T < R',
            't_eq_r': 'T ~ R',
            't_gt_r': 'T > R',
        }
        conc_label = concentration_labels.get(self.result_dm_step1_concentration, '?')
        comp_label = comparison_labels.get(self.result_dm_step2_2_comparison, '?')
        return {
            'verdict': 'fail',
            'message': f'No se encontró escenario para: Concentración {conc_label}, Comparación {comp_label}',
            'scenario_id': False
        }

    def _find_decision_matrix_scenario(self, concentration, control_visible, comparison):
        """
        Busca el escenario coincidente en la matriz de decisión.
        
        Args:
            concentration: 'low', 'medium', 'high'
            control_visible: bool - True si línea C es visible
            comparison: 't_neq_r', 't_lt_r', 't_eq_r', 't_gt_r' o None
            
        Returns:
            recordset: El escenario encontrado o recordset vacío
        """
        self.ensure_one()
        
        if not self.specification_config_id or not self.specification_config_id.specification_id:
            return self.env['amunet.quality.parameter.decision.matrix']
        
        spec = self.specification_config_id.specification_id
        
        if not spec.decision_matrix_scenario_ids:
            return self.env['amunet.quality.parameter.decision.matrix']
        
        DecisionMatrix = self.env['amunet.quality.parameter.decision.matrix']
        
        # Usar el método de búsqueda del modelo
        return DecisionMatrix.find_matching_scenario(
            specification_id=spec.id,
            concentration=concentration,
            control_visible=control_visible,
            comparison=comparison
        )

    def _evaluate_mavi_07(self):
        """Evalúa MAVI-07: Visualización de Líneas Resultado"""
        if not self.mavi07_sample_type or not self.mavi07_observed_result:
            return {'verdict': 'pending', 'message': 'Complete la información del test'}

        if self.mavi07_sample_type == 'negative':
            # Esperamos #5
            if self.mavi07_observed_result == 'result_5':
                return {'verdict': 'pass', 'message': '#5 (Esperado para negativa)'}
            else:
                return {'verdict': 'fail', 'message': f'{self.mavi07_observed_result} (Esperado #5)'}

        elif self.mavi07_sample_type == 'positive':
            # Esperamos #1, #2, #3 o #4 (cualquiera menos #5)
            if self.mavi07_observed_result in ['result_1', 'result_2', 'result_3', 'result_4']:
                return {'verdict': 'pass', 'message': f'{self.mavi07_observed_result} (Esperado #1-#4)'}
            else:
                return {'verdict': 'fail', 'message': '#5 (Esperado #1-#4 para positiva)'}

        return {'verdict': 'pending', 'message': 'Configuración incompleta'}

    def _evaluate_vama_034(self):
        """Evalúa VAMA-034: 2 Pasos (Negativo/Positivo)"""
        if not self.vama034_sample_type or not self.vama034_observed_result:
            return {'verdict': 'pending', 'message': 'Complete la información del test'}

        if self.vama034_sample_type == 'negative':
            if self.vama034_observed_result == 'control_only':
                return {'verdict': 'pass', 'message': 'Opción A: Visualización sólo de la línea control.'}
            else:
                return {'verdict': 'fail', 'message': 'Opción B: Visualización de línea control y línea de prueba. (Esperado Opción A)'}

        elif self.vama034_sample_type == 'positive':
            if self.vama034_observed_result == 'control_test':
                return {'verdict': 'pass', 'message': 'Opción B: Visualización de línea control y línea de prueba.'}
            else:
                return {'verdict': 'fail', 'message': 'Opción A: Visualización sólo de la línea control. (Esperado Opción B)'}

        return {'verdict': 'pending', 'message': 'Configuración incompleta'}

    def _evaluate_vama_006(self):
        """Evalúa VAMA-006: Escala de Color NPS (rango 3-10)"""
        val = self.vama006_color_value
        if val is None or val < 0:
            return {'verdict': 'pending', 'message': 'Seleccione la tonalidad observada (0-14)'}
        if 3 <= val <= 10:
            return {'verdict': 'pass', 'message': f'Tonalidad {val}: Dentro de rango (3-10)'}
        else:
            return {'verdict': 'fail', 'message': f'Tonalidad {val}: Fuera de rango (3-10)'}

    def _evaluate_vama_067(self):
        """Evalúa VAMA-067: Tolerancia a la centrifugación (2 pasos)"""
        if not self.vama067_particles:
            return {'verdict': 'pending', 'message': 'Seleccione el resultado de Partículas (Paso 1)'}
        if not self.vama067_color:
            return {'verdict': 'pending', 'message': 'Seleccione el Color de la Solución (Paso 2)'}

        particles_pass = (self.vama067_particles == 'no_particles')
        color_pass = (self.vama067_color == 'similar_color')

        if particles_pass and color_pass:
            return {'verdict': 'pass', 'message': 'Opción A + Opción A: Cumple (Sin partículas y Color similar)'}
        else:
            reasons = []
            if not particles_pass:
                reasons.append('Con partículas oscuras (Opción B)')
            if not color_pass:
                reasons.append('Color distinto (Opción B)')
            return {'verdict': 'fail', 'message': 'No cumple: ' + ', '.join(reasons)}

    def _evaluate_multi_condition_numeric(self):
        """Evalúa Multi-Condición Numérica (VAMA-096)"""
        # Verificar que todos los campos estén completados
        # Usar campos _filled para verificar si fueron llenados
        if not self.multi_cond_binary:
            return {'verdict': 'pending', 'message': 'Complete todos los campos'}
        if not self.multi_cond_num1_filled:
            return {'verdict': 'pending', 'message': 'Complete todos los campos'}
        if not self.multi_cond_num2_filled:
            return {'verdict': 'pending', 'message': 'Complete todos los campos'}

        # Las 3 condiciones deben cumplirse
        condition1 = self.multi_cond_binary == 'correct'
        condition2 = self.multi_cond_num1 >= self.multi_cond_num1_min
        condition3 = (self.multi_cond_num2_min <= self.multi_cond_num2 <= self.multi_cond_num2_max)

        if condition1 and condition2 and condition3:
            return {
                'verdict': 'pass',
                'message': self.multi_cond_result_text
            }
        else:
            return {
                'verdict': 'fail',
                'message': self.multi_cond_result_text
            }

    def _evaluate_vama_044(self):
        """Evalúa VAMA-044: Funcionalidad de Tubo (4 condiciones)"""
        # Verificar que todos los campos estén completados
        # Usar campos _filled para verificar si fueron llenados
        if not self.vama044_num_gotas_filled:
            return {'verdict': 'pending', 'message': 'Complete todas las condiciones'}
        if not self.vama044_vol_gota_filled:
            return {'verdict': 'pending', 'message': 'Complete todas las condiciones'}
        if not self.vama044_union:
            return {'verdict': 'pending', 'message': 'Complete todas las condiciones'}
        if not self.vama044_vol_llenado_filled:
            return {'verdict': 'pending', 'message': 'Complete todas las condiciones'}
        
        # Las 4 condiciones deben cumplirse
        cond1 = self.vama044_num_gotas >= self.vama044_num_gotas_min
        cond2 = (self.vama044_vol_gota_min <= self.vama044_vol_gota <= self.vama044_vol_gota_max)
        cond3 = (self.vama044_union == 'adequate')
        cond4 = (self.vama044_vol_llenado_min <= self.vama044_vol_llenado <= self.vama044_vol_llenado_max)
        
        if cond1 and cond2 and cond3 and cond4:
            return {
                'verdict': 'pass',
                'message': self.vama044_result_text
            }
        else:
            return {
                'verdict': 'fail',
                'message': self.vama044_result_text
            }

    def _evaluate_vama_112(self):
        """Evalúa VAMA-112: Multi-Checkbox Centrífuga"""
        if not all([self.vama112_cond1, self.vama112_cond2, self.vama112_cond3,
                    self.vama112_cond4, self.vama112_cond5]):
            return {'verdict': 'pending', 'message': 'Complete todas las condiciones'}
        
        # Todas las 5 condiciones deben ser la opción positiva
        all_pass = (
            self.vama112_cond1 == 'adequate' and
            self.vama112_cond2 == 'no_abrupt' and
            self.vama112_cond3 == 'correct' and
            self.vama112_cond4 == 'complete' and
            self.vama112_cond5 == 'no_heat'
        )
        
        if all_pass:
            return {
                'verdict': 'pass',
                'message': self.vama112_result_text if hasattr(self, 'vama112_result_text') else 'Condiciones aceptables'
            }
        else:
            return {
                'verdict': 'fail',
                'message': self.vama112_result_text if hasattr(self, 'vama112_result_text') else 'No cumple todas las condiciones'
            }

    def _evaluate_vama_105(self):
        """Evalúa VAMA-105: Volumen Micropipeta
        
        Criterios según documentación:
        - 5 µL ±2 µL (rango: 3-7 µL)
        - 25 µL ±5 µL (rango: 20-30 µL)
        - 50 µL ±5 µL (rango: 45-55 µL)
        """
        if not self.vama105_nominal_volume:
            return {'verdict': 'pending', 'message': 'Seleccione volumen nominal'}
        if not self.vama105_measured_volume:
            return {'verdict': 'pending', 'message': 'Ingrese el volumen medido'}
            
        try:
            nominal = float(self.vama105_nominal_volume)
        except ValueError:
            return {'verdict': 'pending', 'message': 'Volumen nominal inválido'}
            
        measured = float(self.vama105_measured_volume)
        
        # Rangos de tolerancia según documentación
        tolerance_rules = {
            5: {'min': 3, 'max': 7, 'tolerance': 2},
            25: {'min': 20, 'max': 30, 'tolerance': 5},
            50: {'min': 45, 'max': 55, 'tolerance': 5}
        }
        
        # Buscar regla aplicable (convertir a int para coincidir con claves del diccionario)
        rule = tolerance_rules.get(int(nominal))
        if rule:
            min_val = rule['min']
            max_val = rule['max']
        else:
            # Fallback: tolerancia genérica 5%
            tolerance = max(nominal * 0.05, 0.5)
            min_val = nominal - tolerance
            max_val = nominal + tolerance
        
        if min_val <= measured <= max_val:
            return {
                'verdict': 'pass',
                'message': f'Volumen dispensado de micropipeta {measured} µL'
            }
        else:
            return {
                'verdict': 'fail',
                'message': f'{measured} µL fuera de rango ({nominal} µL: {min_val}-{max_val})'
            }

    def _evaluate_mavi_15_ternary(self):
        """Evalúa MAVI-15: Selección Ternaria (Opción A cumple, B y C fallan)"""
        if not self.mavi15_result:
            return {'verdict': 'pending', 'message': 'Seleccione una opción (A/B/C)'}

        if self.mavi15_result == 'opcion_a':
            return {
                'verdict': 'pass', 
                'message': 'Opción A: Si coincide.'
            }
        elif self.mavi15_result == 'opcion_b':
            return {
                'verdict': 'fail', 
                'message': 'Opción B: No coincide. (Esperado Opción A)'
            }
        elif self.mavi15_result == 'opcion_c':
            return {
                'verdict': 'fail', 
                'message': 'Opción C: Sin visualización de la línea control pese a la coincidencia con el patrón colorimétrico. (Esperado Opción A)'
            }
            
        return {'verdict': 'pending', 'message': 'Opción no reconocida'}

    def _evaluate_mga_0981(self):
        """Evalúa MGA-0981: Variación de volumen"""
        vol_declarado = self.mga0981_vol_declarado
        vol_obtenido = self.mga0981_vol_obtenido

        if not vol_declarado:
            return {'verdict': 'pending', 'message': 'Seleccione volumen declarado'}
        if not vol_obtenido:
            return {'verdict': 'pending', 'message': 'Ingrese la medición obtenida'}

        try:
            nominal = float(vol_declarado.replace('ml', '').strip())
        except ValueError:
            return {'verdict': 'pending', 'message': 'Volumen declarado inválido'}

        # Tolerancia es ± 0.5 ml según la captura/UI y JS
        min_val = nominal - 0.5
        max_val = nominal + 0.5

        if min_val <= vol_obtenido <= max_val:
            return {
                'verdict': 'pass',
                'message': f'Cumple (Medido: {vol_obtenido} ml, Rango: {min_val}-{max_val} ml)'
            }
        else:
            return {
                'verdict': 'fail',
                'message': f'Fuera de rango (Medido: {vol_obtenido} ml, Rango: {min_val}-{max_val} ml)'
            }

    def _evaluate_mavi_11_height(self):
        """Evalúa MAVI-11: Altura del colector (6 u 8 cm)"""
        # Si se usa como conditional_numeric_range, este método no se llama.
        # Si se deja como mavi_11_height, necesita campos específicos.
        # Por ahora, usamos la lógica de rango condicional si está disponible.
        if self.result_conditional_option_id:
            return self._evaluate_conditional_numeric_range()
            
        # Fallback a mavi11_measured_height si existe (Legacy)
        if hasattr(self, 'mavi11_measured_height') and self.mavi11_measured_height:
            val = self.mavi11_measured_height
            # Criterio general ± 0.5 cm
            if 5.5 <= val <= 6.5:
                return {'verdict': 'pass', 'message': f'Cumple 6 cm (Medido: {val})'}
            if 7.5 <= val <= 8.5:
                return {'verdict': 'pass', 'message': f'Cumple 8 cm (Medido: {val})'}
            return {'verdict': 'fail', 'message': f'Fuera de rango 6/8 cm (Medido: {val})'}
            
        return {'verdict': 'pending', 'message': 'Seleccione opción e ingrese medida'}

    def _evaluate_vama_078(self):
        """Evalúa VAMA-078: Multi-Visual Liofilizado"""
        if not all([self.vama078_color, self.vama078_forma,
                    self.vama078_textura, self.vama078_humedad]):
            return {'verdict': 'pending', 'message': 'Complete todas las características visuales'}
        
        # La combinación correcta es: Blanco, Compacto, Sin pegajosa, Sin humedad
        all_correct = (
            self.vama078_color == 'white' and
            self.vama078_forma == 'compact' and
            self.vama078_textura == 'no_sticky' and
            self.vama078_humedad == 'no_moisture'
        )
        
        if all_correct:
            return {
                'verdict': 'pass',
                'message': self.vama078_result_text
            }
        else:
            return {
                'verdict': 'fail',
                'message': self.vama078_result_text
            }

    def _evaluate_vama_multi_check(self):
        """Evalúa VAMA Multi-Check genérico (vama_multi_check, mavi_07_ternary, mavi_07).
        
        Usa el campo multi_check_results_json (o result_text_pattern como fallback)
        y el text_phrase_mapping de la especificación para calcular el dictamen.
        
        Soporta evaluación con rangos de tolerancia mediante la sección 'evaluation' en el mapping.
        """
        import json as _json

        # 1. Obtener mapping de posiciones
        config = self.specification_config_id
        raw_mapping = config.text_phrase_mapping if config else None
        if not raw_mapping and self.specification_id:
            raw_mapping = self.specification_id.text_phrase_mapping
        # Fallback: usar el text_phrase_mapping del propio registro
        if not raw_mapping and self.text_phrase_mapping:
            raw_mapping = self.text_phrase_mapping

        positions = []
        evaluation_rules = None
        if raw_mapping:
            try:
                mapping = _json.loads(raw_mapping)
                positions = mapping.get('positions', [])
                evaluation_rules = mapping.get('evaluation', None)
            except Exception:
                positions = []

        if not positions:
            return {'verdict': 'pending', 'message': 'Configure los puntos de verificación'}

        # 2. Obtener resultados guardados en JSON
        results = {}
        raw_results = self.multi_check_results_json
        if raw_results:
            try:
                results = _json.loads(raw_results)
            except Exception:
                pass

        # Fallback: intentar leer de result_text_pattern (legado, separado por coma)
        if not results and self.result_text_pattern:
            parts = self.result_text_pattern.split(',')
            for i, val in enumerate(parts):
                results[str(i)] = val.strip().upper()

        # 3. Evaluar cada posición
        if not results:
            return {'verdict': 'pending', 'message': 'Complete todos los puntos de la prueba'}

        pending = []
        failed = []
        numeric_messages = []
        select_value = None  # Para guardar el valor seleccionado y usar en evaluación numérica
        
        # Obtener mensajes configurados del mapping
        success_message = mapping.get('success_message', 'Todos los puntos cumplen')
        error_prefix = mapping.get('error_prefix', 'No cumple:')
        dynamic_error = mapping.get('dynamic_error', False)
        error_messages = []  # Para errores dinámicos
        
        for i, pos in enumerate(positions):
            val = results.get(str(i), '')
            ptype = pos.get('type', 'binary')
            label = pos.get('label', f'Posición {i+1}')

            if not val or val == '':
                # Solo es pendiente si no tiene valor
                pending.append(label)
            elif ptype == 'ternary':
                # Tipo ternary: A = Coincide (pass), B = No coincide (fail), N = No aplica (neutral)
                # 'N' NO se considera pendiente ni fallo - se trata como "pase"
                if val == 'B':
                    # Solo B (No coincide) es un fallo
                    error_msg = pos.get('error_msg', f'{label} no coincide.')
                    if dynamic_error:
                        error_messages.append(f"• {error_msg}")
                    else:
                        failed.append(label)
                # A (Coincide) y N (No aplica) se consideran como pass
            elif ptype == 'binary':
                # A = opción positiva (pass), B = opción negativa (fail)
                expected_pass = pos.get('pass_value', 'A')
                if val != expected_pass:
                    failed.append(label)
            elif ptype == 'select':
                # Guardar el valor seleccionado para evaluación posterior
                select_value = val
                # For select types, any non-empty selection is valid
                expected_pass = pos.get('pass_value', None)
                if expected_pass and val != expected_pass:
                    failed.append(label)
            elif ptype == 'numeric':
                # Evaluación numérica con rangos de tolerancia
                try:
                    numeric_val = float(val)
                    
                    # Si hay reglas de evaluación y un valor select previo
                    if evaluation_rules and select_value:
                        eval_type = evaluation_rules.get('type', '')
                        rules = evaluation_rules.get('rules', {})
                        
                        if eval_type == 'volume_tolerance' and select_value in rules:
                            rule = rules[select_value]
                            min_val = rule.get('min', 0)
                            max_val = rule.get('max', 0)
                            tolerance = rule.get('tolerance', 0)
                            
                            if min_val <= numeric_val <= max_val:
                                numeric_messages.append(f'{label}: {numeric_val} uL (OK: {min_val}-{max_val})')
                            else:
                                failed.append(f'{label}: {numeric_val} uL fuera de rango ({min_val}-{max_val})')
                        else:
                            # Sin regla específica, verificar min/max de la posición
                            pos_min = pos.get('min')
                            pos_max = pos.get('max')
                            if pos_min is not None and pos_max is not None:
                                if pos_min <= numeric_val <= pos_max:
                                    numeric_messages.append(f'{label}: {numeric_val}')
                                else:
                                    error_msg = pos.get('error_msg', f'{label}: {numeric_val} fuera de rango ({pos_min}-{pos_max})')
                                    if dynamic_error:
                                        error_messages.append(f"• {error_msg}")
                                    else:
                                        failed.append(f'{label}: fuera de rango')
                            elif pos_min is not None:
                                if numeric_val >= pos_min:
                                    numeric_messages.append(f'{label}: {numeric_val}')
                                else:
                                    error_msg = pos.get('error_msg', f'{label}: {numeric_val} debe ser >= {pos_min}')
                                    if dynamic_error:
                                        error_messages.append(f"• {error_msg}")
                                    else:
                                        failed.append(f'{label}: fuera de rango')
                            else:
                                numeric_messages.append(f'{label}: {numeric_val}')
                    else:
                        # Sin reglas de evaluación, verificar min/max de la posición
                        pos_min = pos.get('min')
                        pos_max = pos.get('max')
                        if pos_min is not None and pos_max is not None:
                            if pos_min <= numeric_val <= pos_max:
                                numeric_messages.append(f'{label}: {numeric_val}')
                            else:
                                error_msg = pos.get('error_msg', f'{label}: {numeric_val} fuera de rango ({pos_min}-{pos_max})')
                                if dynamic_error:
                                    error_messages.append(f"• {error_msg}")
                                else:
                                    failed.append(f'{label}: fuera de rango')
                        elif pos_min is not None:
                            if numeric_val >= pos_min:
                                numeric_messages.append(f'{label}: {numeric_val}')
                            else:
                                error_msg = pos.get('error_msg', f'{label}: {numeric_val} debe ser >= {pos_min}')
                                if dynamic_error:
                                    error_messages.append(f"• {error_msg}")
                                else:
                                    failed.append(f'{label}: fuera de rango')
                        else:
                            numeric_messages.append(f'{label}: {numeric_val}')
                        
                except (ValueError, TypeError):
                    pending.append(f'{label}: valor inválido')

        # 4. Evaluación especial: MAVI-07 con reglas sample_type/result
        if evaluation_rules and 'rules' in evaluation_rules and isinstance(evaluation_rules.get('rules'), list):
            # Nuevo formato: rules es una lista de reglas con sample_type, result, verdict, message
            rules_list = evaluation_rules.get('rules', [])
            
            # Obtener valores de sample_type (índice 0) y result (índice 1)
            sample_type = results.get('0', '')
            result_value = results.get('1', '')
            
            if not sample_type:
                return {'verdict': 'pending', 'message': 'Seleccione el tipo de muestra'}
            if not result_value:
                return {'verdict': 'pending', 'message': 'Seleccione el resultado observado'}
            
            # Buscar la regla que coincide
            for rule in rules_list:
                rule_sample = rule.get('sample_type', '')
                rule_result = rule.get('result', '')
                
                if rule_sample == sample_type and rule_result == result_value:
                    verdict = rule.get('verdict', 'pending')
                    message = rule.get('message', '')
                    return {'verdict': verdict, 'message': message}
            
            # Si no se encontró regla específica, retornar pendiente
            return {'verdict': 'pending', 'message': 'Combinación no configurada'}

        # 5. Evaluación especial: expected_vs_obtained (formato anterior)
        if evaluation_rules and evaluation_rules.get('type') == 'expected_vs_obtained':
            expected_idx = str(evaluation_rules.get('expected_index', 0))
            obtained_idx = str(evaluation_rules.get('obtained_index', 1))
            expected_val = results.get(expected_idx, '')
            obtained_val = results.get(obtained_idx, '')
            
            if not expected_val:
                return {'verdict': 'pending', 'message': 'Seleccione el tipo de muestra (Paso 1)'}
            if not obtained_val:
                return {'verdict': 'pending', 'message': 'Seleccione el resultado obtenido (Paso 2)'}
            
            # Etiquetas simplificadas
            expected_label = 'Muestra negativa' if expected_val == 'negative' else 'Muestra positiva'
            obtained_label = 'Negativo' if obtained_val == 'negative' else 'Positivo'
            
            # Comparar: si coinciden -> pass, si no -> fail
            if expected_val == obtained_val:
                return {
                    'verdict': 'pass',
                    'message': f'{expected_label}: {obtained_label}.'
                }
            else:
                expected_result = 'Negativo' if expected_val == 'negative' else 'Positivo'
                return {
                    'verdict': 'fail',
                    'message': f'{expected_label}: Esperado {expected_result}, Obtenido {obtained_label}.'
                }

        if pending:
            return {'verdict': 'pending', 'message': 'Complete: ' + ', '.join(pending)}

        # Manejo de errores dinámicos (para tipo ternary con dynamic_error=true)
        if error_messages:
            # Construir mensaje dinámico listando solo los fallos
            error_text = '\n'.join(error_messages)
            return {
                'verdict': 'fail',
                'message': f"{error_prefix}\n{error_text}"
            }

        if failed:
            return {
                'verdict': 'fail',
                'message': error_prefix + ' ' + ', '.join(failed)
            }

        # Construir mensaje de éxito usando success_message si está configurado
        msg_parts = []
        if select_value:
            msg_parts.append(f'Volumen nominal: {select_value} uL')
        if numeric_messages:
            msg_parts.extend(numeric_messages)
        
        # Usar success_message configurado o construir uno por defecto
        if success_message and not msg_parts:
            return {'verdict': 'pass', 'message': success_message}
        else:
            message = ' | '.join(msg_parts) if msg_parts else success_message
            return {'verdict': 'pass', 'message': message}

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

    @api.depends('evaluation_type', 'result_selection', 'result_numeric',
                 'result_checkbox_1', 'result_checkbox_2',
                 'result_conditional_option_id', 'result_conditional_value',
                 'result_text_pattern', 'result_expected_type', 'result_obtained_type',
                 'result_binary_option', 'result_ternary', 'uom_id', 'mavi15_result',
                 'result_dm_step1_concentration', 'result_dm_step2_1_control_visible',
                 'result_dm_step2_2_comparison',
                 'mavi07_sample_type', 'mavi07_observed_result',
                 'mavi07_hm_sample_type', 'mavi07_hm_result',
                 'mavi11_target_height', 'mavi11_measured_height',
                 'mga0981_vol_declarado', 'mga0981_vol_obtenido',
                 'vama105_nominal_volume', 'vama105_measured_volume',
                 'vama034_sample_type', 'vama034_observed_result',
                 'multi_cond_binary', 'multi_cond_num1', 'multi_cond_num2')
    def _compute_result_display(self):
        """Genera texto de resultado para mostrar"""
        for record in self:
            if record.evaluation_type == 'binary_selection':
                record.result_display = record.result_selection or ''

            elif record.evaluation_type == 'numeric_range':
                if record.result_numeric is not None:
                    uom = record.uom_id.name if record.uom_id else ''
                    record.result_display = f'{record.result_numeric} {uom}'.strip()
                else:
                    record.result_display = ''

            elif record.evaluation_type == 'checkbox_combined':
                parts = []
                if record.result_checkbox_1:
                    parts.append('✓')
                else:
                    parts.append('✗')
                if record.result_checkbox_2:
                    parts.append('✓')
                else:
                    parts.append('✗')
                record.result_display = ' '.join(parts)

            elif record.evaluation_type == 'conditional_numeric_range':
                if record.result_conditional_option_id and record.result_conditional_value:
                    opt = record.result_conditional_option_id
                    uom = opt.uom_id.name if opt.uom_id else ''
                    record.result_display = f'{record.result_conditional_value} {uom} ({opt.name})'
                else:
                    record.result_display = ''

            elif record.evaluation_type == 'text_pattern':
                record.result_display = record.result_text_pattern or ''

            elif record.evaluation_type == 'expected_vs_obtained':
                if record.result_expected_type and record.result_obtained_type:
                    record.result_display = f'{record.result_expected_type} / {record.result_obtained_type}'
                else:
                    record.result_display = ''

            elif record.evaluation_type == 'binary_with_notes':
                if record.result_binary_option == 'pass':
                    record.result_display = record.binary_notes_option_pass or 'Cumple'
                elif record.result_binary_option == 'fail':
                    record.result_display = record.binary_notes_option_fail or 'No cumple'
                else:
                    record.result_display = ''

            elif record.evaluation_type == 'ternary_with_na':
                ternary_labels = {
                    'yes': record.ternary_option_yes or 'Sí',
                    'no': record.ternary_option_no or 'No',
                    'na': record.ternary_option_na or 'N/A',
                }
                record.result_display = ternary_labels.get(record.result_ternary, '')

            elif record.evaluation_type == 'decision_matrix':
                # Mostrar los pasos completados
                concentration_labels = {
                    'low': 'Baja',
                    'medium': 'Intermedia',
                    'high': 'Alta',
                }
                comparison_labels = {
                    't_neq_r': 'T≠R',
                    't_lt_r': 'T<R',
                    't_eq_r': 'T~R',
                    't_gt_r': 'T>R',
                }
                parts = []
                if record.result_dm_step1_concentration:
                    parts.append(f"1️⃣ {concentration_labels.get(record.result_dm_step1_concentration, '?')}")
                if record.result_dm_step2_1_control_visible:
                    ctrl = 'Sí' if record.result_dm_step2_1_control_visible == 'yes' else 'No'
                    parts.append(f"2️⃣ C:{ctrl}")
                if record.result_dm_step2_2_comparison:
                    parts.append(f"3️⃣ {comparison_labels.get(record.result_dm_step2_2_comparison, '?')}")
                record.result_display = ' → '.join(parts) if parts else ''

            elif record.evaluation_type == 'mavi_07':
                if record.mavi07_sample_type and record.mavi07_observed_result:
                    sample_label = 'Neg' if record.mavi07_sample_type == 'negative' else 'Pos'
                    result_labels = {'result_1': '#1', 'result_2': '#2', 'result_3': '#3', 'result_4': '#4', 'result_5': '#5'}
                    record.result_display = f"{sample_label}: {result_labels.get(record.mavi07_observed_result)}"
                else:
                    record.result_display = ''

            elif record.evaluation_type == 'multi_condition_numeric':
                if all([record.multi_cond_binary, record.multi_cond_num1, record.multi_cond_num2]):
                    func = 'OK' if record.multi_cond_binary == 'correct' else 'ERR'
                    record.result_display = f"{func} | {record.multi_cond_num1} gotas | {record.multi_cond_num2} µl"
                else:
                    record.result_display = ''

            elif record.evaluation_type == 'mavi_15_ternary':
                mavi15_labels = {
                    'opcion_a': 'Opción A: Si coincide.',
                    'opcion_b': 'Opción B: No coincide.',
                    'opcion_c': 'Opción C: Sin visualización de la línea control pese a la coincidencia con el patrón colorimétrico.',
                }
                record.result_display = mavi15_labels.get(record.mavi15_result, '')

            elif record.evaluation_type == 'mga_0981':
                if record.mga0981_vol_declarado and record.mga0981_vol_obtenido:
                    record.result_display = f"{record.mga0981_vol_declarado}: {record.mga0981_vol_obtenido} ml"
                else:
                    record.result_display = ''

            elif record.evaluation_type == 'vama_105':
                if record.vama105_nominal_volume and record.vama105_measured_volume:
                    record.result_display = f"{record.vama105_nominal_volume} µL: {record.vama105_measured_volume} µL"
                else:
                    record.result_display = ''

            elif record.evaluation_type == 'vama_034':
                if record.vama034_sample_type and record.vama034_observed_result:
                    record.result_display = f"{record.vama034_sample_type} → {record.vama034_observed_result}"
                else:
                    record.result_display = ''

            elif record.evaluation_type == 'mavi_11_height':
                if record.mavi11_target_height and record.mavi11_measured_height:
                    record.result_display = f"{record.mavi11_target_height}: {record.mavi11_measured_height} cm"
                else:
                    record.result_display = ''

            elif record.evaluation_type == 'mavi_07_ternary':
                if record.mavi07_hm_sample_type and record.mavi07_hm_result:
                    record.result_display = f"{record.mavi07_hm_sample_type}: {record.mavi07_hm_result}"
                else:
                    record.result_display = ''

            else:
                record.result_display = ''

    @api.depends('specification_config_id', 'specification_config_id.active_conditional_option_ids', 'evaluation_type')
    def _compute_available_conditional_options(self):
        """Obtiene las opciones condicionales disponibles desde la configuración del producto"""
        for record in self:
            if (record.specification_config_id and 
                record.evaluation_type == 'conditional_numeric_range' and
                record.specification_config_id.active_conditional_option_ids):
                record.available_conditional_option_ids = record.specification_config_id.active_conditional_option_ids
            else:
                # Si no hay configuración o no es condicional, usar opciones de la especificación base
                if record.specification_id and record.evaluation_type == 'conditional_numeric_range':
                    record.available_conditional_option_ids = record.specification_id.conditional_option_ids.filtered('active')
                else:
                    record.available_conditional_option_ids = False

    # ========== Onchange ==========

    @api.onchange('result_text_pattern')
    def _onchange_result_text_pattern(self):
        """Convierte a mayúsculas y actualiza la frase construida"""
        if self.result_text_pattern:
            self.result_text_pattern = self.result_text_pattern.upper()
            # Actualizar frase construida para vista previa inmediata
            if self.evaluation_type == 'text_pattern' and self.text_phrase_mapping:
                self.constructed_phrase = self._build_phrase_from_pattern()

    @api.onchange('result_conditional_option_id')
    def _onchange_result_conditional_option_id(self):
        """Al seleccionar opción condicional, muestra el rango"""
        # El rango se muestra a través del campo related de la opción
        pass

    @api.onchange('result_checkbox_1', 'result_checkbox_2')
    def _onchange_checkbox_result(self):
        """Marca como confirmado cuando el usuario interactúa con checkboxes"""
        if self.evaluation_type == 'checkbox_combined':
            self.checkbox_result_confirmed = True

    @api.onchange('result_dm_step2_1_control_visible')
    def _onchange_dm_control_visible(self):
        """
        Si la línea C cambia a 'no', limpiar la comparación
        ya que el paso 2.2 se bloquea.
        """
        if self.evaluation_type == 'decision_matrix':
            if self.result_dm_step2_1_control_visible == 'no':
                self.result_dm_step2_2_comparison = False

    @api.onchange('result_dm_step1_concentration')
    def _onchange_dm_concentration(self):
        """
        Al cambiar la concentración, limpiar los pasos siguientes
        para forzar re-evaluación.
        """
        if self.evaluation_type == 'decision_matrix':
            # Solo limpiar si no hay valor en paso 2.1 todavía
            # o si queremos forzar re-evaluación completa
            pass  # Por ahora no limpiamos para permitir cambios sin perder datos

    # ========== Métodos de Utilidad ==========

    def get_selection_options(self):
        """Retorna las opciones de selección según el tipo de evaluación"""
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

    def get_obtained_options(self):
        """Retorna las opciones de resultado obtenido para expected_vs_obtained"""
        self.ensure_one()
        if self.evaluation_type == 'expected_vs_obtained':
            obtained_list = [opt.strip() for opt in (self.obtained_options or '').split(',') if opt.strip()]
            return [(opt, opt) for opt in obtained_list]
        return []

    @api.model
    def unlink(self):
        """Prevent deletion of Test Line Details once the QC is out of 'draft' state."""
        for record in self:
            if record.check_id.state != 'draft':
                raise ValidationError("No se pueden eliminar detalles de prueba si el control de calidad no está en estado 'Borrador'.")
        return super(AmunetQualityTestLineDetail, self).unlink()
