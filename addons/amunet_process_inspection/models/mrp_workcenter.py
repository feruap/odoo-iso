# -*- coding: utf-8 -*-
from odoo import models, fields


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    inspection_type = fields.Selection(
        selection=[
            ('qc_formal', 'Inspeccion QC formal'),
            ('production_supervision', 'Supervision de produccion'),
        ],
        string='Tipo de inspeccion requerida',
        help='Define que tipo de inspeccion de proceso se crea '
             'automaticamente al confirmar una orden de produccion '
             'que pase por esta estacion. Si esta vacio, no se crea '
             'inspeccion para esta estacion.',
    )
