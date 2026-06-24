# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = 'product.category'

    amunet_prefijo = fields.Char(
        string='Prefijo de clave',
        size=6,
        help="Prefijo de la clave para productos NUEVOS de esta categoria "
             "(ej. MPCAR para Materia prima/Cartucho). La clave se forma con este "
             "prefijo + consecutivo de 2 digitos. Definido por PNOAL-005 / Documentacion.")
