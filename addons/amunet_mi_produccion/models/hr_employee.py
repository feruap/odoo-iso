# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Puesto de piso = las estaciones (centros de trabajo) donde la persona
    # trabaja. "Mi dia" muestra solo las actividades de esas estaciones.
    # Origen: Actividades_Produccion.xlsx de RRHH (3-sep-2026): Soluciones y
    # Laminado para la ruta larga; Corte, Encartuchado y Acondicionado para
    # la ruta corta.
    amunet_mi_workcenter_ids = fields.Many2many(
        'mrp.workcenter',
        'amunet_mi_employee_workcenter_rel',
        'employee_id', 'workcenter_id',
        string='Estaciones donde trabaja',
        help='Estaciones de produccion que atiende esta persona. En "Mi dia" '
             'solo ve las actividades de estas estaciones. Sin estaciones '
             'asignadas ve todas (comportamiento anterior).')
