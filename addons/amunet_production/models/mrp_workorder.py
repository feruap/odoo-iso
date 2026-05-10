# -*- coding: utf-8 -*-
from odoo import models


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def button_start(self):
        """Valida calibraciones de los equipos del WC antes de arrancar.

        Si algun equipo vinculado a workcenter_id.amunet_equipment_ids
        no tiene calibracion vigente, button_start levanta UserError
        (gracias a _amunet_check_equipment_calibration en mrp.workcenter).
        """
        for wo in self:
            wc = wo.workcenter_id
            if wc:
                wc._amunet_check_equipment_calibration()
        return super().button_start()
