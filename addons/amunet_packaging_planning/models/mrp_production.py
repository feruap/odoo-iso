# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    packaging_plan_ids = fields.One2many(
        'amunet.packaging.plan',
        'production_id',
        string='Planes de empaque',
    )
    packaging_plan_count = fields.Integer(
        string='Planes de empaque',
        compute='_compute_packaging_plan_count',
    )

    def _compute_packaging_plan_count(self):
        for rec in self:
            rec.packaging_plan_count = len(rec.packaging_plan_ids)

    def action_create_packaging_plan(self):
        self.ensure_one()
        existing = self.packaging_plan_ids.filtered(lambda plan: plan.state not in ('cancel',))
        if existing:
            return existing[0].action_generate_suggestion() or {
                'type': 'ir.actions.act_window',
                'name': _('Plan de empaque'),
                'res_model': 'amunet.packaging.plan',
                'view_mode': 'form',
                'res_id': existing[0].id,
            }
        plan = self.env['amunet.packaging.plan'].create({
            'production_id': self.id,
        })
        plan.action_generate_suggestion()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Plan de empaque'),
            'res_model': 'amunet.packaging.plan',
            'view_mode': 'form',
            'res_id': plan.id,
        }

    def action_view_packaging_plans(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Planes de empaque'),
            'res_model': 'amunet.packaging.plan',
            'view_mode': 'list,form',
            'domain': [('production_id', '=', self.id)],
            'context': {'default_production_id': self.id},
        }

    def action_confirm(self):
        """Gate de Amunet: para MOs con route_type 'short' o 'long', no
        permitir confirmar sin un plan de empaque APROBADO (o cerrado).
        Razon: el plan define las presentaciones a fabricar y por tanto
        la cantidad de empaque secundario que debe surtir almacen. Sin
        plan no se puede dimensionar el surtido.

        Soluciones y resale no requieren plan (no se empacan en
        presentaciones secundarias).
        """
        for prod in self:
            route_type = getattr(prod, 'route_type', False)
            if route_type in ('short', 'long'):
                aprobados = prod.packaging_plan_ids.filtered(
                    lambda p: p.state in ('approved', 'done')
                )
                if not aprobados:
                    raise UserError(_(
                        'Antes de confirmar la orden %(mo)s, aprueba un '
                        'plan de empaque. El plan define las presentaciones '
                        'a fabricar y cuanta caja/etiqueta debe surtir '
                        'almacen.\n\n'
                        'Pulsa el boton "Planear empaque" para crearlo, '
                        'genera la sugerencia, ajusta si es necesario y '
                        'aprueba antes de confirmar.'
                    ) % {'mo': prod.name})
        return super().action_confirm()
