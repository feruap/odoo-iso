# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AmunetAnalysisWizard(models.TransientModel):
    _name = 'amunet.production.analysis.wizard'
    _description = 'Wizard de Confirmación de Análisis de Solución'

    production_id = fields.Many2one('mrp.production', string='Orden de Producción', required=True)
    product_id = fields.Many2one(related='production_id.product_id', string='Solución a Analizar', readonly=True)
    quality_ph_initial = fields.Float(related='production_id.quality_ph_initial', string='pH Inicial', readonly=True)
    quality_ph_final = fields.Float(related='production_id.quality_ph_final', string='pH Final', readonly=True)
    product_qty = fields.Float(related='production_id.product_qty', string='Cantidad a Producir', readonly=True)
    amunet_expiration_text = fields.Char(related='production_id.amunet_expiration_text', string='Caducidad Declarada', readonly=True)
    solution_expiration_date = fields.Datetime(related='production_id.solution_expiration_date', string='Fecha de Caducidad', readonly=True)
    solution_lot_id = fields.Char(related='production_id.solution_lot_id', string='Lote Asignado', readonly=True)
    
    # We show the lines that were used
    move_raw_ids = fields.One2many(related='production_id.move_raw_ids', readonly=True)

    def action_confirm_analysis(self):
        """Cambia estado a Analisis Solicitado, pasa a En Progreso y crea el QC"""
        self.ensure_one()
        self.production_id.write({
            'quality_analysis_status': 'requested'
        })

        # Confirmar la orden si aun esta en borrador, luego pasar a En Progreso
        if self.production_id.state == 'draft':
            self.production_id.action_confirm()
        if self.production_id.state == 'confirmed':
            self.production_id.action_start()

        # Creacion del QC en Calidad Amunet
        self.env['amunet.quality.check'].sudo().create({
            'product_id': self.product_id.id,
            'company_id': self.production_id.company_id.id,
            'amunet_production_id': self.production_id.id,
        })

        return {'type': 'ir.actions.act_window_close'}
