# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_quality_control = fields.Boolean(
        string='Es Control de Calidad',
        compute='_compute_is_quality_control',
        store=True,
        help='Indica si este picking es de control de calidad'
    )

    is_storage = fields.Boolean(
        string='Es almacenamiento',
        compute='_compute_is_storage',
        store=True,
        help='Indica si este picking es de almacenamiento'
    )

    is_reception = fields.Boolean(
        string='Es recepción',
        compute='_compute_is_reception',
        store=True,
        help='Indica si este picking es de recepción'
    )

    @api.depends('picking_type_id', 'picking_type_id.is_quality_control')
    def _compute_is_quality_control(self):
        """Calcula si este picking es de control de calidad"""
        for record in self:
            record.is_quality_control = (
                record.picking_type_id.is_quality_control
                if record.picking_type_id else False
            )

    @api.depends('picking_type_id', 'picking_type_id.is_storage')
    def _compute_is_storage(self):
        """Calcula si este picking es de almacenamiento"""
        for record in self:
            record.is_storage = (
                record.picking_type_id.is_storage
                if record.picking_type_id else False
            )

    @api.depends('picking_type_id', 'picking_type_id.is_reception')
    def _compute_is_reception(self):
        """Calcula si este picking es de recepción"""
        for record in self:
            record.is_reception = (
                record.picking_type_id.is_reception
                if record.picking_type_id else False
            )

    def action_confirm(self):
        """
        Override para intentar reservar automáticamente en entradas.
        Esto soluciona el problema de que las recepciones queden "En Espera".
        """
        res = super(StockPicking, self).action_confirm()

        # Intentar reservar (Check Availability) automáticamente para entradas
        for picking in self:
            if picking.picking_type_code == 'incoming' and picking.state == 'confirmed':
                try:
                    picking.action_assign()
                    
                    # Si después de intentar reservar sigue sin estar listo (ej. viene de tránsito sin stock),
                    # y es una recepción, FORZAMOS el estado a disponible.
                    if picking.state not in ('assigned', 'done', 'cancel'):
                        picking.move_ids.write({'state': 'assigned'})
                        # El estado del picking se recalcula automáticamente
                        
                except Exception as e:
                    # Si falla, intentamos forzar
                    picking.move_ids.write({'state': 'assigned'})
        return res

    def _action_done(self):
        """
        Override para sincronizar factory_lot_id de stock.move.line a stock.lot
        después de validar el picking.
        """
        res = super()._action_done()
        
        # Sincronizar campos de las líneas a los lotes
        for picking in self:
            for line in picking.move_line_ids:
                if line.lot_id:
                    vals_sync = {}
                    if line.factory_lot_id and line.lot_id.factory_lot_id != line.factory_lot_id:
                        vals_sync['factory_lot_id'] = line.factory_lot_id.id
                    if line.manufacturing_date and line.lot_id.manufacturing_date != line.manufacturing_date:
                        vals_sync['manufacturing_date'] = line.manufacturing_date
                    if line.expiration_date and line.lot_id.expiration_date != line.expiration_date:
                        vals_sync['expiration_date'] = line.expiration_date
                    if line.removal_date and line.lot_id.removal_date != line.removal_date:
                        vals_sync['removal_date'] = line.removal_date
                    
                    if vals_sync:
                        line.lot_id.sudo().write(vals_sync)
        
        return res

