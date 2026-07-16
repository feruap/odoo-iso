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
                mo = check.amunet_production_id

                # "en el qc cuando este en el estado de "Pendiente recepcion almacen" igual se marcara como confirmado en produccion"
                if new_state == 'awaiting_reception':
                    mo.quality_analysis_status = 'approved'
                    # Custodia de Calidad (Opcion B): al APROBAR se produce el
                    # terminado de la SOLUCION en Control de calidad (destino ya
                    # ruteado ahi) ANTES de que la disposicion del QC genere la
                    # recepcion Control de calidad -> existencias (que Almacen
                    # valida) y merme el muestreo. Asi el stock ya existe cuando
                    # la recepcion lo necesita. No-soluciones conservan el flujo
                    # original (producen al finalizar el QC).
                    if mo.amunet_is_solution_product and mo.state not in ('done', 'cancel'):
                        # Registrar la cantidad producida y producir saltando los
                        # asistentes de MRP (consumo vs BoM y backorder): el consumo
                        # real ya se capturo en el flujo y la solucion se produce
                        # completa. Asi el terminado queda posteado en Control de
                        # calidad antes de que corra la disposicion del QC.
                        if not mo.qty_producing:
                            mo.qty_producing = mo.product_qty
                        mo.with_context(
                            skip_consumption=True,
                            skip_backorder=True,
                        ).button_mark_done()

                # "y cuando sea "finalizado" este en produccion sera "Hecho""
                elif new_state == 'done':
                    if check.amunet_production_id.quality_analysis_status != 'approved':
                        check.amunet_production_id.quality_analysis_status = 'approved'
                        
                    # Validar de forma bruta primero que el botón sea invocable
                    if check.amunet_production_id.state not in ['done', 'cancel']:
                        check.amunet_production_id.button_mark_done()
                        
        return res
