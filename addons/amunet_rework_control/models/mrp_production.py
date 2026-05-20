# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    rework_order_ids = fields.One2many(
        'amunet.rework.order',
        'production_id',
        string='No conformidades / reprocesos',
    )
    rework_order_count = fields.Integer(
        string='Reprocesos',
        compute='_compute_rework_order_count',
    )

    @api.depends('rework_order_ids')
    def _compute_rework_order_count(self):
        for rec in self:
            rec.rework_order_count = len(rec.rework_order_ids)

    def action_create_rework_order(self):
        self.ensure_one()
        lot_name = self.solution_lot_id or ', '.join(self.lot_producing_ids.mapped('name'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('No conformidad / reproceso'),
            'res_model': 'amunet.rework.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_production_id': self.id,
                'default_product_id': self.product_id.id,
                'default_lot_id': self.lot_producing_ids[:1].id if self.lot_producing_ids else False,
                'default_lot_name': lot_name,
                'default_title': _('Reproceso en %s') % (self.name or self.product_id.display_name),
                'default_qty_nonconforming': self.product_qty,
                'default_containment_action': '<p>%s</p>' % _('Produccion retiene el lote/sub-lote hasta disposicion de Calidad.'),
            },
        }

    def action_view_rework_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('No conformidades / reprocesos'),
            'res_model': 'amunet.rework.order',
            'view_mode': 'list,form',
            'domain': [('production_id', '=', self.id)],
            'context': {'default_production_id': self.id},
        }
