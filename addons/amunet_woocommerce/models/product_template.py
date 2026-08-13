# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    amunet_linea_larga = fields.Boolean(
        string='Línea larga (fabricación)', default=False, index=True,
        help='Marca manual: el producto se fabrica en LÍNEA LARGA. '
             'Mientras se ajustan las rutas de BoM de línea larga, este '
             'marcador define el "Tipo de Fabricación" en la vista de '
             'mapeos Woo. Cuando la ruta del BoM ya sea de línea larga, '
             'el cálculo la tomará de ahí y este marcador queda redundante.')
