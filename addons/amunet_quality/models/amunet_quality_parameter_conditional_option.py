# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AmunetQualityParameterConditionalOption(models.Model):
    """
    Opción Condicional de Especificación.

    Representa una opción de volumen/rango para parámetros de tipo
    conditional_numeric_range (ej: VAMA-105 - Volumen de micropipeta).

    Cada opción define un valor nominal y un rango (min/max) que se usa
    para evaluar el valor medido cuando el analista selecciona esa opción.

    Epic-031: Sistema de Parámetros de Calidad Jerárquicos
    T-031-13: Implementar evaluación condicional numérica
    """
    _name = 'amunet.quality.parameter.conditional.option'
    _description = 'Opción Condicional de Especificación'
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
        string='Secuencia',
        default=10,
        help='Orden de la opción'
    )

    # ========== Identificación ==========

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre de la opción (ej: 5 µL, 100 µL, 1000 µL)'
    )

    # ========== Configuración de Rango ==========

    nominal_value = fields.Float(
        string='Valor nominal',
        digits='Product Unit of Measure',
        help='Valor nominal de referencia (ej: 5, 100, 500)'
    )

    tolerance = fields.Float(
        string='Tolerancia (±)',
        digits='Product Unit of Measure',
        help='Tolerancia aplicada al valor nominal para calcular min/max'
    )

    min_value = fields.Float(
        string='Valor mínimo',
        digits='Product Unit of Measure',
        required=True,
        help='Valor mínimo aceptable para esta opción'
    )

    max_value = fields.Float(
        string='Valor máximo',
        digits='Product Unit of Measure',
        required=True,
        help='Valor máximo aceptable para esta opción'
    )

    uom_id = fields.Many2one(
        'uom.uom',
        string='Unidad de medida',
        help='Unidad de medida (ej: µL, mL)'
    )

    # ========== Control ==========

    is_not_applicable = fields.Boolean(
        string='Es No Aplica',
        default=False,
        help='Si está marcado, seleccionar esta opción devuelve veredicto N/A sin requerir valor numérico'
    )

    active = fields.Boolean(
        string='Activo',
        default=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        related='specification_id.company_id',
        store=True
    )

    # ========== Campos Computados ==========

    display_name = fields.Char(
        string='Nombre completo',
        compute='_compute_display_name',
        store=True
    )

    range_display = fields.Char(
        string='Rango',
        compute='_compute_range_display',
        store=True
    )

    @api.depends('name', 'min_value', 'max_value', 'uom_id')
    def _compute_display_name(self):
        """Genera nombre con rango: '5 µL (3-7)'"""
        for record in self:
            uom_name = record.uom_id.name if record.uom_id else ''
            record.display_name = f"{record.name} ({record.min_value}-{record.max_value} {uom_name})".strip()

    @api.depends('min_value', 'max_value', 'uom_id')
    def _compute_range_display(self):
        """Genera texto de rango: '3-7 µL'"""
        for record in self:
            uom_name = record.uom_id.name if record.uom_id else ''
            record.range_display = f"{record.min_value}-{record.max_value} {uom_name}".strip()

    # ========== Onchange ==========

    @api.onchange('nominal_value', 'tolerance')
    def _onchange_nominal_tolerance(self):
        """Calcula min/max desde nominal y tolerancia"""
        if self.nominal_value and self.tolerance:
            self.min_value = self.nominal_value - self.tolerance
            self.max_value = self.nominal_value + self.tolerance

    # ========== Métodos de Evaluación ==========

    def evaluate_value(self, measured_value):
        """
        Evalúa si un valor medido está dentro del rango de esta opción.

        Args:
            measured_value: Valor numérico medido por el analista

        Returns:
            dict: {'verdict': 'pass'|'fail', 'message': str}
        """
        self.ensure_one()

        if measured_value is None:
            return {'verdict': 'pending', 'message': 'Ingrese el valor medido'}

        uom_name = self.uom_id.name if self.uom_id else ''

        if self.min_value <= measured_value <= self.max_value:
            return {
                'verdict': 'pass',
                'message': f'{measured_value} {uom_name} dentro de rango ({self.min_value}-{self.max_value})'
            }
        else:
            return {
                'verdict': 'fail',
                'message': f'{measured_value} {uom_name} fuera de rango ({self.min_value}-{self.max_value})'
            }

    # ========== Constraints ==========

    @api.constrains('min_value', 'max_value')
    def _check_range(self):
        """Valida que min <= max"""
        for record in self:
            if record.min_value > record.max_value:
                raise ValidationError(
                    f'El valor mínimo ({record.min_value}) no puede ser mayor al máximo ({record.max_value})'
                )





