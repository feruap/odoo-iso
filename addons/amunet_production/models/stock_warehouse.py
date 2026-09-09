# -*- coding: utf-8 -*-
from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    amunet_loc_piso_id = fields.Many2one(
        'stock.location',
        string='Piso de producción',
        domain="[('usage','=','internal')]",
        help='Ubicación donde vive el material que ya salió del anaquel y '
             'todavía no se consume. Se llena al recibir el surtido y se '
             'vacía cuando Almacén firma la conciliación. Si está vacía, la '
             'orden avisa y el material no se mueve.')
