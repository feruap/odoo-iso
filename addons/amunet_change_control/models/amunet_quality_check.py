# -*- coding: utf-8 -*-

from odoo import fields, models, _


class AmunetQualityCheck(models.Model):
    _inherit = 'amunet.quality.check'

    change_control_ids = fields.One2many(
        'amunet.change.control',
        'quality_check_id',
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
        production = self.env['mrp.production']
        if 'amunet_production_id' in self._fields:
            production = self.amunet_production_id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nueva desviacion / cambio'),
            'res_model': 'amunet.change.control',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_title': _('Desviacion / cambio desde %s') % self.name,
                'default_product_id': self.product_id.id,
                'default_lot_id': self.lot_id.id,
                'default_quality_check_id': self.id,
                'default_production_id': production.id if production else False,
                'default_scope': 'lot',
            },
        }

    def action_view_change_controls(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Desviaciones y cambios'),
            'res_model': 'amunet.change.control',
            'view_mode': 'list,form',
            'domain': [('quality_check_id', '=', self.id)],
            'context': {
                'default_product_id': self.product_id.id,
                'default_lot_id': self.lot_id.id,
                'default_quality_check_id': self.id,
                'default_scope': 'lot',
            },
        }
