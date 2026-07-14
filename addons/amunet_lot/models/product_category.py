# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = 'product.category'

    amunet_removal_value = fields.Integer(
        string='Anticipo de remocion',
        default=0,
        help='Cuanto tiempo ANTES de la caducidad se fija la fecha de remocion '
             'de un lote de esta categoria. 0 = hereda de la categoria padre; '
             'si ninguna lo define, se usa 1 mes.')
    amunet_removal_unit = fields.Selection(
        [('days', 'Dias'), ('months', 'Meses')],
        string='Unidad de remocion', default='months')

    def _amunet_get_removal_offset(self):
        """Devuelve (valor, unidad) efectivo del anticipo de remocion, subiendo
        por el arbol de categorias hasta encontrar una que lo defina.
        Default (1, 'months') si ninguna lo configura."""
        self.ensure_one()
        cat = self
        while cat:
            if cat.amunet_removal_value and cat.amunet_removal_value > 0:
                return cat.amunet_removal_value, cat.amunet_removal_unit or 'months'
            cat = cat.parent_id
        return 1, 'months'
