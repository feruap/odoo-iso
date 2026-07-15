# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    amunet_requires_quarantine = fields.Boolean(
        'Requiere inspección de Calidad',
        help='Si está activo, al recibir este material irá a AMP/Control de calidad '
             'antes de pasar a existencias. Si se deja sin marcar, hereda el valor '
             'de la categoría del producto.',
    )

    @api.onchange('categ_id')
    def _onchange_categ_quarantine(self):
        if self.categ_id and not self.amunet_requires_quarantine:
            self.amunet_requires_quarantine = self.categ_id.amunet_requires_quarantine

    def _amunet_effective_requires_quarantine(self):
        """Devuelve True si el producto o su categoría requieren inspección."""
        self.ensure_one()
        return self.amunet_requires_quarantine or self.categ_id.amunet_requires_quarantine
