# -*- coding: utf-8 -*-
from odoo import _, models


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def button_start(self):
        """Valida calibraciones / estado de equipos antes de arrancar.

        Si workcenter_id._amunet_check_equipment_calibration falla,
        levanta UserError. Si pasa pero el WC tiene
        amunet_no_equipment_required=True, registra una nota en el
        chatter de la mrp.production relacionada (mrp.workorder no es
        mail.thread; el log queda en la MO padre, donde es visible y
        auditable).
        """
        for wo in self:
            wc = wo.workcenter_id
            if not wc:
                continue
            res = wc._amunet_check_equipment_calibration() or {}
            if res.get('no_equipment_required') and wo.production_id:
                wo.production_id.message_post(body=_(
                    'WO <b>%s</b> (id=%s) iniciada sin equipos calibrados. '
                    'Workcenter <b>%s</b> esta marcado como '
                    '"No requiere equipo calibrado" '
                    '(amunet_no_equipment_required=True). '
                    'Excepcion autorizada en configuracion del WC. '
                    'Justificacion ISO 13485 debe estar documentada en '
                    'la nota del workcenter o en CAPA.'
                ) % (wo.name or wo.id, wo.id, wc.code or wc.name))
        return super().button_start()
