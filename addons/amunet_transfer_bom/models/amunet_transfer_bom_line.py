# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AmunetTransferBomLine(models.Model):
    _name = 'amunet.transfer.bom.line'
    _description = 'Componentes de lista de materiales para entregas'
    _order = 'sequence, id'

    bom_id = fields.Many2one(
        'amunet.transfer.bom',
        string='Lista de materiales',
        required=True,
        ondelete='cascade',
        index=True
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    product_id = fields.Many2one(
        'product.product',
        string='Componente',
        required=True,
        domain="[('type', 'in', ['product', 'consu'])]",
        index=True
    )
    product_qty = fields.Float(
        string='Cantidad',
        required=True,
        digits='Product Unit of Measure',
        default=1.0
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unidad de medida',
        required=True
    )
    company_id = fields.Many2one(
        'res.company',
        related='bom_id.company_id',
        store=True,
        index=True
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Al seleccionar producto, asignar UoM por defecto"""
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
