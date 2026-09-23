# -*- coding: utf-8 -*-
from odoo import models, fields


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    # Marca la linea de combo que YA se convirtio en hojas. Sin esto la
    # conversion se vuelve a disparar cada vez que el combo se mueve a Entrada
    # o a Control de calidad (p.ej. el AMP/QC que genera la ruta), y cada
    # corrida INVENTA lotes nuevos para las hojas. Paso de verdad: SPHMC85
    # acabo con 4 lotes y el analisis de Calidad se quedo apuntando al primero
    # mientras el material fisico estaba en otro.
    amunet_combo_conv_id = fields.Many2one(
        'stock.picking', string='Conversión de combo generada',
        copy=False, index=True, readonly=True,
        help='Conversión que ya desglosó esta línea de combo en sus hojas. '
             'Si está puesta, la conversión no se vuelve a disparar.')
