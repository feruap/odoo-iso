# -*- coding: utf-8 -*-

from odoo import models


class ProductProduct(models.Model):
    """
    Extensión de product.product para Control de Calidad.

    Agrega el método action_view_quality_checks para que funcione
    tanto desde product.template como desde product.product.
    """
    _inherit = 'product.product'

    def action_view_quality_checks(self):
        """Abre los controles de calidad del producto"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Controles de calidad',
            'res_model': 'amunet.quality.check',
            'view_mode': 'list,form',
            'domain': [('product_id', '=', self.id)],
            'context': {'default_product_id': self.id},
        }







