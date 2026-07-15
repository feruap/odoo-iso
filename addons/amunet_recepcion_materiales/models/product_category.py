# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = 'product.category'

    amunet_requires_quarantine = fields.Boolean(
        'Requiere inspección de Calidad',
        default=False,
        help='Si está activo, todos los productos de esta categoría irán a '
             'AMP/Control de calidad al recibirlos. Se puede sobrescribir por producto.',
    )
