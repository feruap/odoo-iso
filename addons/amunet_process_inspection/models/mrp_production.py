# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    process_inspection_ids = fields.One2many(
        'amunet.process.inspection', 'production_id',
        string='Inspecciones de proceso',
    )
    process_inspection_count = fields.Integer(
        string='Inspecciones',
        compute='_compute_process_inspection_count',
    )

    @api.depends('process_inspection_ids')
    def _compute_process_inspection_count(self):
        for rec in self:
            rec.process_inspection_count = len(rec.process_inspection_ids)

    def action_view_process_inspections(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Inspecciones de proceso'),
            'res_model': 'amunet.process.inspection',
            'view_mode': 'list,form',
            'domain': [('production_id', '=', self.id)],
            'context': {
                'default_production_id': self.id,
                'search_default_production_id': self.id,
            },
        }
