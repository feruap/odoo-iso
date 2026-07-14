# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class MrpRoutingWorkcenter(models.Model):
    """Configuracion por ACTIVIDAD (operacion del routing): controles en
    proceso y EQUIPOS que usa la actividad.

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

    # --- Equipos por actividad (no por todo el centro de trabajo) ---
    amunet_equipment_by_operation = fields.Boolean(
        string='Equipo definido por actividad',
        help='Si esta activo, esta actividad valida SOLO los equipos listados '
             'en "Equipos de la actividad" (aunque sean de otra area), en vez '
             'de todos los equipos del centro de trabajo. Si la lista queda '
             'vacia, la actividad NO requiere equipo. Si esta desactivado, se '
             'valida por centro de trabajo (comportamiento anterior).',
    )
    amunet_equipment_ids = fields.Many2many(
        comodel_name='amunet.equipment',
        relation='amunet_operation_equipment_rel',
        column1='operation_id', column2='equipment_id',
        string='Equipos de la actividad',
        help='Equipos que realmente usa esta actividad. Pueden pertenecer a '
             'otra area (ej. Liberacion la hace Calidad con equipo de '
             'Produccion). Se validan calibracion vigente y estado operativo '
             'al arrancar la orden y en el preflight.',
    )

    def _amunet_check_operation_equipment(self):
        """Valida calibracion/estado de los equipos de ESTA actividad.

        - Si amunet_equipment_by_operation: valida SOLO amunet_equipment_ids
          (lista vacia = la actividad no requiere equipo -> pasa).
        - Si no: delega al centro de trabajo (comportamiento anterior), para
          que las operaciones aun no migradas sigan validando como hoy.
        Devuelve dict {'no_equipment_required': bool}. Levanta UserError si hay
        problemas de calibracion/estado.
        """
        self.ensure_one()
        if not self.amunet_equipment_by_operation:
            if self.workcenter_id:
                return self.workcenter_id._amunet_check_equipment_calibration()
            return {'no_equipment_required': True}
        equipments = self.amunet_equipment_ids
        if not equipments:
            return {'no_equipment_required': True}
        label = self.name or (self.workcenter_id.code or self.workcenter_id.name or '')
        problemas = self.env['mrp.workcenter']._amunet_calibration_problems_for(
            equipments, label)
        if problemas:
            raise UserError(_(
                'No se puede iniciar la actividad "%(act)s". Problemas de '
                'equipo:\n%(probs)s\n\n'
                'Sube certificados de calibracion vigentes o reactiva los '
                'equipos antes de arrancar.'
            ) % {'act': self.name or '', 'probs': '\n'.join(problemas)})
        return {'no_equipment_required': False}
