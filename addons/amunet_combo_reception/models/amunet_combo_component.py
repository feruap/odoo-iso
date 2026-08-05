# -*- coding: utf-8 -*-
from odoo import models, fields


class AmunetComboComponent(models.Model):
    """Componente de un combo de compra: define en qué producto(s) reales se
    convierte el combo al recibirlo (ej. combo Zika -> SPHMC61 + SPHMC62)."""
    _name = 'amunet.combo.component'
    _description = 'Componente de combo de compra'
    _order = 'sequence, id'

    combo_tmpl_id = fields.Many2one(
        'product.template', string='Combo', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one(
        'product.product', string='Producto real (hoja/insumo)', required=True)
    qty = fields.Float(
        string='Cantidad por combo', default=1.0,
        digits='Product Unit of Measure',
        help='Cuánto de este componente sale por cada unidad de combo recibida.')
    product_uom_id = fields.Many2one(
        'uom.uom', string='UdM',
        related='product_id.uom_id', readonly=True)
