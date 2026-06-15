# -*- coding: utf-8 -*-
from odoo import models, fields


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    amunet_supervisor_ids = fields.Many2many(
        'res.users',
        'amunet_mi_workcenter_supervisor_rel',
        'workcenter_id', 'user_id',
        string='Supervisores responsables',
        help='Usuarios responsables de supervisar las actividades de esta '
             'estacion. En "Mis supervisiones", cada supervisor ve solo las '
             'actividades de las estaciones donde esta asignado como '
             'responsable (los gerentes de manufactura ven todas).')
