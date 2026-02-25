# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AmunetQualityAdditionalInfoConfig(models.Model):
    _name = 'amunet.quality.additional.info.config'
    _description = 'Configuración de información adicional por producto'
    _order = 'sequence, id'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Producto',
        required=True,
        ondelete='cascade',
        index=True,
        help='Producto al que aplica esta configuración'
    )

    field_id = fields.Many2one(
        comodel_name='amunet.quality.additional.info.field',
        string='Campo',
        required=True,
        ondelete='cascade',
        domain=[('active', '=', True)],
        help='Campo informativo a capturar'
    )

    # Campos relacionados para mostrar en vista
    field_name = fields.Char(
        string='Nombre del campo',
        related='field_id.name',
        readonly=True,
        store=False
    )

    field_type_display = fields.Selection(
        string='Tipo',
        related='field_id.field_type',
        readonly=True,
        store=False
    )

    uom = fields.Char(
        string='Unidad',
        related='field_id.uom',
        readonly=True,
        store=False
    )

    placeholder = fields.Char(
        string='Placeholder',
        related='field_id.placeholder',
        readonly=True,
        store=False
    )

    required = fields.Boolean(
        string='Obligatorio',
        default=False,
        help='Si está marcado, el campo será obligatorio al ejecutar el QC'
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Si está desmarcado, este campo no aparecerá en el QC'
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de visualización en el QC (menor = primero)'
    )

    @api.constrains('product_tmpl_id', 'field_id')
    def _check_product_field_unique(self):
        """Validar que no haya campos duplicados para un producto."""
        for record in self:
            existing = self.search([
                ('product_tmpl_id', '=', record.product_tmpl_id.id),
                ('field_id', '=', record.field_id.id),
                ('id', '!=', record.id),
            ], limit=1)
            if existing:
                raise ValidationError(
                    'Este campo ya está configurado para este producto. No se puede duplicar.'
                )
