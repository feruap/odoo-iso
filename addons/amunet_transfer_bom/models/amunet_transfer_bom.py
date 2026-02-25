# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AmunetTransferBom(models.Model):
    _name = 'amunet.transfer.bom'
    _description = 'Lista de Materiales para Entregas'
    _order = 'product_id, id'

    name = fields.Char(
        string='Referencia',
        compute='_compute_name',
        store=True,
        readonly=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Producto principal',
        required=True,
        domain="[('type', 'in', ['product', 'consu'])]",
        index=True
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        related='product_id.product_tmpl_id',
        string='Plantilla de producto',
        store=True,
        index=True
    )
    product_qty = fields.Float(
        string='Cantidad base',
        default=1.0,
        required=True,
        digits='Product Unit of Measure',
        help='Cantidad base para calcular componentes (normalmente 1.0)'
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unidad de medida',
        required=True
    )
    bom_line_ids = fields.One2many(
        'amunet.transfer.bom.line',
        'bom_id',
        string='Componentes'
    )
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
        required=True
    )

    @api.depends('product_id', 'product_qty')
    def _compute_name(self):
        for bom in self:
            if bom.product_id:
                bom.name = f"BOM - {bom.product_id.display_name}"
            else:
                bom.name = "Lista de materiales"

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Asignar UoM por defecto al seleccionar producto"""
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id

    @api.constrains('product_id', 'company_id')
    def _check_product_unique(self):
        """Validar que solo exista una lista de materiales por producto en cada compañía."""
        for record in self:
            existing = self.search([
                ('product_id', '=', record.product_id.id),
                ('company_id', '=', record.company_id.id),
                ('id', '!=', record.id),
            ], limit=1)
            if existing:
                raise ValidationError(
                    'Solo puede existir una lista de materiales por producto en cada compañía.'
                )
