# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AmunetQualityCheck(models.Model):
    _inherit = 'amunet.quality.check'

    rework_order_ids = fields.One2many(
        'amunet.rework.order',
        'origin_quality_check_id',
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
        title = _('Reproceso por falla en %s') % (self.name or self.product_id.display_name)
        return {
            'type': 'ir.actions.act_window',
            'name': _('No conformidad / reproceso'),
            'res_model': 'amunet.rework.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_origin_quality_check_id': self.id,
                'default_product_id': self.product_id.id,
                'default_lot_id': self.lot_id.id,
                'default_lot_name': self.lot_id.name or self.lot_name_amunet,
                'default_title': title,
                'default_failed_parameter_summary': self.fail_reason,
                'default_failure_description': '<p>%s</p>' % (self.fail_reason or _('Falla detectada en control de calidad.')),
                'default_qty_nonconforming': self.qty_sampling or self.lot_qty_available,
                'default_containment_action': '<p>%s</p>' % _('Lote retenido/no liberado hasta disposicion de Calidad.'),
            },
        }

    def action_view_rework_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('No conformidades / reprocesos'),
            'res_model': 'amunet.rework.order',
            'view_mode': 'list,form',
            'domain': [('origin_quality_check_id', '=', self.id)],
            'context': {'default_origin_quality_check_id': self.id},
        }
