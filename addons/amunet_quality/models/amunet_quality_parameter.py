# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AmunetQualityParameter(models.Model):
    """
    Catálogo de Parámetros de Calidad.

    Define las determinaciones/pruebas que pueden aplicarse a los productos.
    Soporta jerarquía de especificaciones para parámetros compuestos.

    Epic-031: Sistema de Parámetros de Calidad Jerárquicos
    HU-031-1: Configurar Plantillas de Parámetros con Especificaciones
    """
    _name = 'amunet.quality.check.parameter'
    _description = 'Parámetro de Control de Calidad'
    _order = 'code, name'

    # ========== Campos de Identificación ==========

    code = fields.Char(
        string='Código',
        required=True,
        index=True,
        help='Código del parámetro (ej: MAVI-04, VAMA-112). '
             'Nota: El código NO es único, puede reutilizarse en múltiples parámetros.'
    )

    name = fields.Char(
        string='Determinación',
        required=True,
        help='Nombre de la prueba o determinación'
    )

    # ========== Especificaciones (NUEVO en Epic-031) ==========

    specification_line_ids = fields.One2many(
        'amunet.quality.check.parameter.specification',
        'parameter_id',
        string='Especificaciones',
        help='Líneas de especificación del parámetro'
    )

    specification_count = fields.Integer(
        string='Cant. Especificaciones',
        compute='_compute_specification_count',
        store=True
    )

    is_hierarchical = fields.Boolean(
        string='Especificaciones jerárquicas',
        compute='_compute_is_hierarchical',
        store=True,
        help='True si tiene más de 1 especificación'
    )

    # ========== Control ==========

    active = fields.Boolean(
        string='Activo',
        default=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company
    )

    # ========== Campos Computados ==========

    @api.depends('specification_line_ids')
    def _compute_specification_count(self):
        """Cuenta las especificaciones del parámetro"""
        for record in self:
            record.specification_count = len(record.specification_line_ids)

    @api.depends('specification_count')
    def _compute_is_hierarchical(self):
        """Determina si el parámetro tiene jerarquía de especificaciones"""
        for record in self:
            record.is_hierarchical = record.specification_count > 1

    # ========== Métodos de Acción ==========

    def action_view_specifications(self):
        """Abre vista de especificaciones del parámetro"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Especificaciones - {self.code}',
            'res_model': 'amunet.quality.check.parameter.specification',
            'view_mode': 'list,form',
            'domain': [('parameter_id', '=', self.id)],
            'context': {
                'default_parameter_id': self.id,
            },
        }

    def action_create_default_specification(self):
        """Crea una especificación por defecto con tipo de evaluación binary_selection"""
        self.ensure_one()

        if self.specification_line_ids:
            return  # Ya tiene especificaciones

        # Crear una especificación con el tipo de evaluación más común por defecto
        self.env['amunet.quality.check.parameter.specification'].create({
            'parameter_id': self.id,
            'name': self.name,
            'acceptance_criteria': self.name,
            'evaluation_type': 'binary_selection',
            'sequence': 10,
        })

    # ========== Métodos de Evaluación ==========

    def evaluate_result(self, result_value):
        """
        Evalúa un resultado contra la especificación del parámetro.

        Delega la evaluación a la primera especificación del parámetro.

        Args:
            result_value: Valor del resultado (float para numérico, str para selección)

        Returns:
            str: 'pass' si cumple, 'fail' si no cumple, 'pending' si no hay valor
        """
        self.ensure_one()

        if not self.specification_line_ids:
            return 'pending'

        # Delegar a la primera especificación
        spec = self.specification_line_ids[0]
        result = spec.evaluate_result({'selection': result_value, 'numeric': result_value})
        return result.get('verdict', 'pending')

    # ========== Métodos de Utilidad ==========

    def copy_specifications_to_product(self, product_tmpl_id, rel_id):
        """
        Copia las especificaciones del parámetro a la configuración del producto.
        
        Args:
            product_tmpl_id: ID del product.template
            rel_id: ID del amunet.quality.parameter.product.rel
        """
        self.ensure_one()
        SpecConfig = self.env['amunet.quality.parameter.specification.config']
        
        for spec in self.specification_line_ids:
            SpecConfig.create({
                'product_parameter_rel_id': rel_id,
                'specification_id': spec.id,
                'active': True,
                'sequence': spec.sequence,
            })

    # ========== NOTA: Constraint de unicidad de código ELIMINADO ==========
    # El constraint _check_unique_code fue eliminado para permitir
    # reutilización de códigos (ej: MAVI-04 puede existir múltiples veces)
    # Referencia: T-031-3
