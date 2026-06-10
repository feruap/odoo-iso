# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    reanalysis_extension_months = fields.Integer(
        string='Meses de extensión (reanálisis)',
        default=0,
        help='Meses que se extiende la caducidad si el reanálisis aprueba. '
             '0 = no aplica reanálisis para esta categoría.',
    )

    reanalysis_applies = fields.Boolean(
        string='Aplica reanálisis por caducidad',
        compute='_compute_reanalysis_applies',
        store=True,
    )

    @api.depends('reanalysis_extension_months')
    def _compute_reanalysis_applies(self):
        for cat in self:
            cat.reanalysis_applies = cat.reanalysis_extension_months > 0
