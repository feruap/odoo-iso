# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    pilot_preflight_ids = fields.One2many(
        'amunet.pilot.preflight',
        'production_id',
        string='Preflights piloto',
    )
    pilot_preflight_count = fields.Integer(
        string='Preflights',
        compute='_compute_pilot_preflight_count',
    )
    amunet_preflight_accepted = fields.Boolean(
        string='Piloto aceptado',
        compute='_compute_amunet_preflight_accepted',
        store=True,
    )

    def _compute_pilot_preflight_count(self):
        for rec in self:
            rec.pilot_preflight_count = len(rec.pilot_preflight_ids)

    @api.depends('pilot_preflight_ids.state')
    def _compute_amunet_preflight_accepted(self):
        for rec in self:
            rec.amunet_preflight_accepted = any(
                p.state == 'accepted' for p in rec.pilot_preflight_ids
            )

    def action_run_pilot_preflight(self):
        self.ensure_one()
        preflight = self.pilot_preflight_ids[:1]
        if not preflight:
            preflight = self.env['amunet.pilot.preflight'].create({
                'production_id': self.id,
                'product_id': self.product_id.id,
                'product_qty': self.product_qty,
                'bom_id': self.bom_id.id or False,
                'company_id': self.company_id.id,
            })
        preflight.action_run_checks()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Preflight del piloto'),
            'res_model': 'amunet.pilot.preflight',
            'view_mode': 'form',
            'res_id': preflight.id,
        }

    def action_view_pilot_preflights(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Preflights piloto'),
            'res_model': 'amunet.pilot.preflight',
            'view_mode': 'list,form',
            'domain': [('production_id', '=', self.id)],
            'context': {'default_production_id': self.id},
        }
