# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = 'product.category'

    amunet_route_to_aru = fields.Boolean(
        string='Reactivo -> Almacen de reactivos en uso',
        help='Si esta activo, al surtir por Solicitud de Material un producto de '
             'esta categoria, la transferencia se dirige al Almacen de reactivos '
             'en uso (ARU) en lugar del consumo normal. Las subcategorias '
             'heredan de la categoria padre.')

    def _amunet_routes_to_aru(self):
        """True si esta categoria (o alguna ancestro) esta marcada para dirigir
        sus productos al Almacen de reactivos en uso (ARU)."""
        self.ensure_one()
        cat = self
        while cat:
            if cat.amunet_route_to_aru:
                return True
            cat = cat.parent_id
        return False
