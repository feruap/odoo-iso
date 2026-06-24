# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    amunet_requires_quarantine = fields.Boolean(
        'Requiere inspección de Calidad',
        help='Si está activo, al recibir este material irá a AMP/Control de calidad '
             'antes de pasar a existencias. Lo define Calidad.',
    )
