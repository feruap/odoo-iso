from odoo import models


class MrpProductionDoc(models.Model):
    _inherit = 'mrp.production'

    def action_reportar_cambio(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reportar cambio / novedad',
            'res_model': 'amunet.reporte.cambio.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_production_id': self.id},
        }
