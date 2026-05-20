# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AmunetAnalysisWizard(models.TransientModel):
    _name = 'amunet.production.analysis.wizard'
    _description = 'Wizard de Confirmación de Análisis de Producción'

    production_id = fields.Many2one('mrp.production', string='Orden de Producción', required=True)
    product_id = fields.Many2one(related='production_id.product_id', string='Producto a Analizar', readonly=True)
    quality_ph_initial = fields.Float(related='production_id.quality_ph_initial', string='pH Inicial', readonly=True)
    quality_ph_final = fields.Float(related='production_id.quality_ph_final', string='pH Final', readonly=True)
    product_qty = fields.Float(related='production_id.product_qty', string='Cantidad a Producir', readonly=True)
    amunet_expiration_text = fields.Char(related='production_id.amunet_expiration_text', string='Caducidad Declarada', readonly=True)
    solution_expiration_date = fields.Datetime(related='production_id.solution_expiration_date', string='Fecha de Caducidad', readonly=True)
    solution_lot_id = fields.Char(related='production_id.solution_lot_id', string='Lote Asignado', readonly=True)
    sampling_plan_id = fields.Many2one(
        'amunet.quality.sampling.plan',
        string='Plan de Muestreo',
        compute='_compute_sampling_preview',
    )
    suggested_qty_sampling = fields.Float(
        string='Muestra Sugerida',
        compute='_compute_sampling_preview',
    )
    sampling_plan_summary = fields.Html(
        string='Criterio de Muestreo',
        compute='_compute_sampling_preview',
    )
    
    # We show the lines that were used
    move_raw_ids = fields.One2many(related='production_id.move_raw_ids', readonly=True)

    @api.depends('product_id', 'product_qty')
    def _compute_sampling_preview(self):
        Plan = self.env['amunet.quality.sampling.plan'].sudo()
        for wizard in self:
            plan = Plan.browse()
            suggested = 0.0
            if wizard.product_id and wizard.product_qty:
                plan = Plan.find_applicable_plan(
                    wizard.product_id,
                    wizard.product_qty,
                    'final_release',
                )
                suggested = plan.compute_sample_qty(wizard.product_qty) if plan else 0.0

            wizard.sampling_plan_id = plan
            wizard.suggested_qty_sampling = suggested
            if plan:
                wizard.sampling_plan_summary = (
                    '<p><b>Liberación final.</b> %s (%s). '
                    'Calidad recibirá sugerencia de <b>%s</b> pieza(s) para muestreo.</p>'
                    % (plan.name, plan.code, suggested)
                )
            else:
                wizard.sampling_plan_summary = (
                    '<p><b>Sin plan de muestreo aplicable.</b> Calidad deberá justificar '
                    'manualmente la cantidad de muestra.</p>'
                )

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
        quality_vals = {
            'product_id': self.product_id.id,
            'company_id': self.production_id.company_id.id,
            'amunet_production_id': self.production_id.id,
            'sampling_stage': 'final_release',
            'original_qty_received': self.production_id.product_qty,
            'sampling_uom_id': self.production_id.product_uom_id.id,
        }
        lot = self.production_id.lot_producing_ids[:1]
        if lot:
            quality_vals['lot_id'] = lot.id

        check = self.env['amunet.quality.check'].sudo().create(quality_vals)
        check._set_sampling_plan_suggestion(force=False)

        return {'type': 'ir.actions.act_window_close'}
