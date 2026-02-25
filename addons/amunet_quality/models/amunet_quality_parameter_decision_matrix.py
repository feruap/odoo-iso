# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AmunetQualityParameterDecisionMatrix(models.Model):
    """
    Matriz de Decisión para Parámetros de Calidad.

    Representa un escenario de evaluación dentro de una matriz de decisión.
    Cada especificación de tipo 'decision_matrix' puede tener múltiples 
    escenarios (ej: MAVI-16 tiene 13 escenarios).

    Epic-031: Sistema de Parámetros de Calidad Jerárquicos
    HU-031-3: Implementar Parámetro con Matriz de Decisión Multi-Paso (MAVI-16)
    T-031-18: Crear modelo amunet.quality.parameter.decision.matrix
    """
    _name = 'amunet.quality.parameter.decision.matrix'
    _description = 'Escenario de Matriz de Decisión'
    _order = 'sequence, id'

    # ========== Relación con Especificación ==========

    specification_id = fields.Many2one(
        'amunet.quality.check.parameter.specification',
        string='Especificación',
        required=True,
        ondelete='cascade',
        index=True
    )

    sequence = fields.Integer(
        string='No. Escenario',
        default=10,
        help='Número del escenario en la matriz (1-13 para MAVI-16)'
    )

    # ========== Paso 1: Concentración Objetivo ==========

    step1_concentration = fields.Selection([
        ('any', 'Cualquiera'),
        ('low', 'Baja'),
        ('medium', 'Intermedia'),
        ('high', 'Alta'),
    ], string='Paso 1: Concentración', required=True, default='low',
        help='Concentración objetivo seleccionada en el paso 1')

    step1_concentration_display = fields.Char(
        string='Concentración (Display)',
        compute='_compute_step1_display'
    )

    # ========== Paso 2.1: Línea de Control Visible ==========

    step2_1_control_visible = fields.Selection([
        ('yes', 'Sí, visible'),
        ('no', 'No visible'),
        ('any', 'Cualquiera'),
    ], string='Paso 2.1: Línea C', required=True, default='yes',
        help='¿La línea de control (C) es visible?')

    # ========== Paso 2.2: Comparación T vs R ==========

    step2_2_comparison = fields.Selection([
        ('t_neq_r', 'T ≠ R (No hay línea T)'),
        ('t_lt_r', 'T < R (Menor intensidad)'),
        ('t_eq_r', 'T ~ R (Intensidad similar)'),
        ('t_gt_r', 'T > R (Mayor intensidad)'),
        ('irrelevant', '(Irrelevante)'),
    ], string='Paso 2.2: T vs R', default='irrelevant',
        help='Comparación visual entre región de prueba (T) y referencia (R)')

    # ========== Resultado ==========

    result_message = fields.Text(
        string='Mensaje del Sistema',
        required=True,
        help='Mensaje que se muestra al encontrar este escenario (configurable)'
    )

    verdict = fields.Selection([
        ('pass', 'Cumple'),
        ('fail', 'No Cumple'),
    ], string='Dictamen', required=True, default='fail',
        help='Resultado del escenario')

    # ========== Control ==========

    active = fields.Boolean(
        string='Activo',
        default=True
    )

    # ========== Campos Computados ==========

    name = fields.Char(
        string='Nombre',
        compute='_compute_name',
        store=True
    )

    @api.depends('sequence', 'step1_concentration', 'step2_1_control_visible', 
                 'step2_2_comparison', 'verdict')
    def _compute_name(self):
        """Genera nombre descriptivo del escenario"""
        concentration_labels = {
            'any': 'Cualquiera',
            'low': 'Baja',
            'medium': 'Intermedia',
            'high': 'Alta',
        }
        comparison_labels = {
            't_neq_r': 'T≠R',
            't_lt_r': 'T<R',
            't_eq_r': 'T~R',
            't_gt_r': 'T>R',
            'irrelevant': '-',
        }
        verdict_labels = {
            'pass': '✅',
            'fail': '❌',
        }
        for record in self:
            conc = concentration_labels.get(record.step1_concentration, '?')
            ctrl = 'Sí' if record.step2_1_control_visible == 'yes' else 'No'
            comp = comparison_labels.get(record.step2_2_comparison, '?')
            verd = verdict_labels.get(record.verdict, '?')
            record.name = f"Escenario {record.sequence}: {conc} + {ctrl} + {comp} → {verd}"

    @api.depends('step1_concentration')
    def _compute_step1_display(self):
        """Genera texto para mostrar la concentración con su expectativa"""
        display_map = {
            'any': 'Cualquiera',
            'low': 'Baja (Se espera: T ≠ R o T < R)',
            'medium': 'Intermedia (Se espera: T ~ R)',
            'high': 'Alta (Se espera: T > R)',
        }
        for record in self:
            record.step1_concentration_display = display_map.get(
                record.step1_concentration, record.step1_concentration
            )

    # ========== Métodos de Búsqueda ==========

    @api.model
    def find_matching_scenario(self, specification_id, concentration, control_visible, comparison):
        """
        Busca el escenario que coincide con los inputs dados.

        Args:
            specification_id: ID de la especificación
            concentration: 'low', 'medium', 'high'
            control_visible: True/False (¿Línea C visible?)
            comparison: 't_neq_r', 't_lt_r', 't_eq_r', 't_gt_r'

        Returns:
            recordset: El escenario encontrado o recordset vacío
        """
        # Primero buscar escenario específico
        domain = [
            ('specification_id', '=', specification_id),
            ('active', '=', True),
        ]

        # Si línea C no es visible, buscar escenario de invalidación (cualquier concentración)
        if not control_visible:
            domain.append(('step2_1_control_visible', '=', 'no'))
            # También aceptar 'any' para control visible
            scenarios = self.search(domain, order='sequence', limit=1)
            if not scenarios:
                # Buscar con 'any'
                domain[-1] = ('step2_1_control_visible', 'in', ['no', 'any'])
                scenarios = self.search(domain, order='sequence', limit=1)
            return scenarios

        # Línea C visible: buscar por concentración y comparación
        domain.extend([
            ('step2_1_control_visible', 'in', ['yes', 'any']),
        ])

        # Buscar primero con concentración específica
        specific_domain = domain + [
            ('step1_concentration', '=', concentration),
            ('step2_2_comparison', '=', comparison),
        ]
        scenarios = self.search(specific_domain, order='sequence', limit=1)

        if not scenarios:
            # Buscar con concentración 'any'
            any_domain = domain + [
                ('step1_concentration', '=', 'any'),
                ('step2_2_comparison', '=', comparison),
            ]
            scenarios = self.search(any_domain, order='sequence', limit=1)

        return scenarios

    # ========== Datos Iniciales para MAVI-16 ==========

    @api.model
    def get_mavi16_default_scenarios(self):
        """
        Retorna la configuración por defecto de los 13 escenarios de MAVI-16.
        Usar para poblar la matriz al crear un parámetro MAVI-16.

        Returns:
            list: Lista de diccionarios con los valores de cada escenario
        """
        return [
            # Escenario 1: Línea C NO visible = Fallo inmediato
            {
                'sequence': 1,
                'step1_concentration': 'any',
                'step2_1_control_visible': 'no',
                'step2_2_comparison': 'irrelevant',
                'verdict': 'fail',
                'result_message': 'Inválido: No hay visualización de la línea de control.',
            },
            # Concentración Baja
            {
                'sequence': 2,
                'step1_concentration': 'low',
                'step2_1_control_visible': 'yes',
                'step2_2_comparison': 't_neq_r',
                'verdict': 'pass',
                'result_message': 'T ≠ R: No hay formación de una línea de color en la región T.',
            },
            {
                'sequence': 3,
                'step1_concentration': 'low',
                'step2_1_control_visible': 'yes',
                'step2_2_comparison': 't_lt_r',
                'verdict': 'pass',
                'result_message': 'T < R: La intensidad de la línea de color en la región T es menos intensa que la línea de color en la región R.',
            },
            {
                'sequence': 4,
                'step1_concentration': 'low',
                'step2_1_control_visible': 'yes',
                'step2_2_comparison': 't_eq_r',
                'verdict': 'fail',
                'result_message': 'Inconsistente: Se esperaba Baja, se observó Intermedia.',
            },
            {
                'sequence': 5,
                'step1_concentration': 'low',
                'step2_1_control_visible': 'yes',
                'step2_2_comparison': 't_gt_r',
                'verdict': 'fail',
                'result_message': 'Inconsistente: Se esperaba Baja, se observó Alta.',
            },
            # Concentración Intermedia
            {
                'sequence': 6,
                'step1_concentration': 'medium',
                'step2_1_control_visible': 'yes',
                'step2_2_comparison': 't_neq_r',
                'verdict': 'fail',
                'result_message': 'Inconsistente: Se esperaba Intermedia, no hubo reacción en T.',
            },
            {
                'sequence': 7,
                'step1_concentration': 'medium',
                'step2_1_control_visible': 'yes',
                'step2_2_comparison': 't_lt_r',
                'verdict': 'fail',
                'result_message': 'Inconsistente: Se esperaba Intermedia, se observó Baja.',
            },
            {
                'sequence': 8,
                'step1_concentration': 'medium',
                'step2_1_control_visible': 'yes',
                'step2_2_comparison': 't_eq_r',
                'verdict': 'pass',
                'result_message': 'T ~ R: La intensidad de la línea de color en la región T es igual o similar en intensidad que la línea de color en la región R.',
            },
            {
                'sequence': 9,
                'step1_concentration': 'medium',
                'step2_1_control_visible': 'yes',
                'step2_2_comparison': 't_gt_r',
                'verdict': 'fail',
                'result_message': 'Inconsistente: Se esperaba Intermedia, se observó Alta.',
            },
            # Concentración Alta
            {
                'sequence': 10,
                'step1_concentration': 'high',
                'step2_1_control_visible': 'yes',
                'step2_2_comparison': 't_neq_r',
                'verdict': 'fail',
                'result_message': 'Inconsistente: Se esperaba Alta, no hubo reacción en T.',
            },
            {
                'sequence': 11,
                'step1_concentration': 'high',
                'step2_1_control_visible': 'yes',
                'step2_2_comparison': 't_lt_r',
                'verdict': 'fail',
                'result_message': 'Inconsistente: Se esperaba Alta, se observó Baja.',
            },
            {
                'sequence': 12,
                'step1_concentration': 'high',
                'step2_1_control_visible': 'yes',
                'step2_2_comparison': 't_eq_r',
                'verdict': 'fail',
                'result_message': 'Inconsistente: Se esperaba Alta, se observó Intermedia.',
            },
            {
                'sequence': 13,
                'step1_concentration': 'high',
                'step2_1_control_visible': 'yes',
                'step2_2_comparison': 't_gt_r',
                'verdict': 'pass',
                'result_message': 'T > R: La intensidad de la línea de color en la región T es más intensa que la línea de color en la región R.',
            },
        ]

    def action_populate_mavi16_scenarios(self):
        """
        Acción para poblar la matriz con los 13 escenarios de MAVI-16.
        Usar desde el botón en la vista de especificación.
        """
        self.ensure_one()
        if not self.specification_id:
            return

        scenarios = self.get_mavi16_default_scenarios()
        for scenario_vals in scenarios:
            scenario_vals['specification_id'] = self.specification_id.id
            self.create(scenario_vals)





