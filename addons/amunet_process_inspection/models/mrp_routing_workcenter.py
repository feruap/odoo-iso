# -*- coding: utf-8 -*-
from odoo import models, fields


class MrpRoutingWorkcenter(models.Model):
    """Configuracion por ACTIVIDAD (operacion del routing) de que
    controles en proceso se generan al confirmar la orden de produccion.

    Sustituye al flag por estacion (mrp.workcenter.inspection_type, ahora
    deprecado): permite distinguir actividades que comparten la misma
    estacion (p.ej. Acondicionado usado en dos pasos distintos).
    """
    _inherit = 'mrp.routing.workcenter'

    amunet_requires_supervision = fields.Boolean(
        string='Requiere supervision',
        help='Si esta activo, al confirmar la orden se genera una '
             'Supervision para esta actividad, que firma el supervisor '
             'de produccion. Una Supervision NO es una inspeccion.',
    )
    amunet_requires_inspection = fields.Boolean(
        string='Requiere inspeccion de Calidad',
        help='Si esta activo, al confirmar la orden se genera una '
             'Inspeccion en proceso para esta actividad, que firma '
             'personal de Calidad.',
    )
