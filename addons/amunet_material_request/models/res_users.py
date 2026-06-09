# -*- coding: utf-8 -*-
from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    amunet_material_head_id = fields.Many2one(
        'res.users',
        string='Jefe de Solicitudes de Material',
        help='Jefe de area que puede VER las Solicitudes de Material '
             'creadas por este usuario (ademas de las propias del jefe). '
             'El jefe debe tener el grupo '
             '"Solicitudes de Material / Jefe de area".',
    )
    amunet_material_requires_head_approval = fields.Boolean(
        string='Requiere autorizacion del jefe para solicitar material',
        help='Si esta activo, las Solicitudes de Material de este usuario '
             'NO van directo a almacen: requieren que su Jefe (campo de '
             'arriba) las AUTORICE primero. Pensado para practicantes.',
    )
