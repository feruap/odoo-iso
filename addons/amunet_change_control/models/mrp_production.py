# -*- coding: utf-8 -*-

from odoo import fields, models, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    change_control_ids = fields.One2many(
        'amunet.change.control',
        'production_id',
        string='Desviaciones y cambios',
    )
    change_control_count = fields.Integer(
        string='Desviaciones/Cambios',
        compute='_compute_change_control_count',
    )

    def _compute_change_control_count(self):
        for record in self:
            record.change_control_count = len(record.change_control_ids)

    def action_create_change_control(self):
        self.ensure_one()
        lot = self.lot_producing_ids[:1]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nueva desviacion / cambio'),
            'res_model': 'amunet.change.control',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_title': _('Desviacion / cambio desde %s') % self.name,
                'default_product_id': self.product_id.id,
                'default_lot_id': lot.id,
                'default_production_id': self.id,
                'default_scope': 'lot',
            },
        }

    def action_view_change_controls(self):
        self.ensure_one()
        lot = self.lot_producing_ids[:1]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Desviaciones y cambios'),
            'res_model': 'amunet.change.control',
            'view_mode': 'list,form',
            'domain': [('production_id', '=', self.id)],
            'context': {
                'default_product_id': self.product_id.id,
                'default_lot_id': lot.id,
                'default_production_id': self.id,
                'default_scope': 'lot',
            },
        }
