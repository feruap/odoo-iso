# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    es_combo_compra = fields.Boolean(
        string='Es combo de compra',
        help='Si está marcado, este producto se compra como 1 SKU (combo del '
             'proveedor) y al recibirlo se convierte en sus componentes reales '
             '(hojas/insumos), cada uno con su lote Amunet.')
    combo_component_ids = fields.One2many(
        'amunet.combo.component', 'combo_tmpl_id',
        string='Componentes del combo')
