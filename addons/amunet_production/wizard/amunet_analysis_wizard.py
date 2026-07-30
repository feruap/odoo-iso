# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AmunetAnalysisWizard(models.TransientModel):
    _name = 'amunet.production.analysis.wizard'
    _description = 'Wizard de Solicitud de Análisis de Producción (simple)'

    production_id = fields.Many2one('mrp.production', string='Orden de Producción', required=True)
    product_id = fields.Many2one(related='production_id.product_id', string='Producto a Analizar', readonly=True)
    product_qty = fields.Float(related='production_id.product_qty', string='Cantidad Planeada', readonly=True)
    amunet_expiration_text = fields.Char(related='production_id.amunet_expiration_text', string='Caducidad Declarada', readonly=True)
    lote_producido = fields.Char(string='Lote', compute='_compute_lote_producido', readonly=True)

    @api.depends('production_id')
    def _compute_lote_producido(self):
        for w in self:
            lots = w.production_id.lot_producing_ids
            w.lote_producido = ', '.join(lots.mapped('name')) if lots else (w.production_id.solution_lot_id or '')

    # Cantidad real de piezas fabricadas con la que se solicita el análisis.
    # Esa cantidad es la que se produce al cerrar la orden.
    qty_fabricada = fields.Float(
        string='Piezas fabricadas',
        required=True,
        help='Cantidad de piezas realmente fabricadas con la que se solicita el análisis. '
             'Esta cantidad es la que se produce al cerrar la orden.',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        prod = self.env['mrp.production'].browse(res.get('production_id')) if res.get('production_id') else False
        if prod:
            res.setdefault('qty_fabricada', prod.qty_producing or prod.product_qty)
        return res

    def action_confirm_analysis(self):
        """Marca el análisis como SOLICITADO (simple) con las piezas fabricadas.

        No crea el análisis del módulo de calidad (eso se engancha después).
        Solo registra la cantidad fabricada y deja la orden lista para que
        Calidad apruebe o rechace con su PIN.
        """
        self.ensure_one()
        if self.qty_fabricada <= 0:
            from odoo.exceptions import UserError
            raise UserError(_('Indica cuántas piezas fabricadas solicitas para el análisis (mayor a 0).'))

        prod = self.production_id
        # Confirmar/arrancar la orden si aún está en borrador
        if prod.state == 'draft':
            prod.action_confirm()
        if prod.state == 'confirmed':
            prod.action_start()

        # Registrar las piezas fabricadas como cantidad a producir
        prod.qty_producing = self.qty_fabricada
        prod.write({
            'quality_analysis_status': 'requested',
            'amunet_pt_qty_solicitada': self.qty_fabricada,
        })
        prod.message_post(body=_(
            'Análisis solicitado con <b>%s</b> pieza(s) fabricada(s). '
            'Pendiente de aprobación de Calidad.'
        ) % self.qty_fabricada)

        return {'type': 'ir.actions.act_window_close'}
