# -*- coding: utf-8 -*-

from odoo import models, fields


class AmunetQualityCheckDestination(models.Model):
    """
    Linea de destino original para un Control de Calidad.
    Registra cada ubicacion y cantidad solicitada antes de redirigir a Cuarentena.
    """
    _name = 'amunet.quality.check.destination'
    _description = 'Destino Original de QC'

    check_id = fields.Many2one(
        'amunet.quality.check',
        string='Control de Calidad',
        required=True,
        ondelete='cascade',
        index=True,
    )

    location_dest_id = fields.Many2one(
        'stock.location',
        string='Ubicacion destino original',
        required=True,
        ondelete='restrict',
    )

    quantity = fields.Float(
        string='Cantidad',
        digits='Product Unit of Measure',
        required=True,
    )
