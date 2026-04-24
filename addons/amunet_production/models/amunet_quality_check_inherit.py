# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AmunetQualityCheck(models.Model):
    _inherit = 'amunet.quality.check'

    amunet_production_id = fields.Many2one('mrp.production', string='Orden de Producción Vinculada', readonly=True)

    def write(self, vals):
        res = super(AmunetQualityCheck, self).write(vals)
        if 'state' in vals:
            for check in self:
                if not check.amunet_production_id:
                    continue
                
                new_state = check.state
                
                # "en el qc cuando este en el estado de "Pendiente recepcion almacen" igual se marcara como confirmado en produccion"
                if new_state == 'awaiting_reception':
                    check.amunet_production_id.quality_analysis_status = 'approved'
                
                # "y cuando sea "finalizado" este en produccion sera "Hecho""
                elif new_state == 'done':
                    if check.amunet_production_id.quality_analysis_status != 'approved':
                        check.amunet_production_id.quality_analysis_status = 'approved'
                        
                    # Validar de forma bruta primero que el botón sea invocable
                    if check.amunet_production_id.state not in ['done', 'cancel']:
                        check.amunet_production_id.button_mark_done()
                        
        return res
