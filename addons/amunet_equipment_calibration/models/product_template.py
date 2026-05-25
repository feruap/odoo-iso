# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    amunet_allow_multi_serial = fields.Boolean(
        string='Permite multiples series por lote',
        default=False,
        help='Si esta activo, un solo lote Amunet de este producto puede '
             'agrupar varias unidades fisicas, cada una con su propio '
             'numero de serie del fabricante. Util para equipos donde '
             'compras varias piezas en un mismo evento pero el lote '
             'Amunet es uno solo.',
    )
