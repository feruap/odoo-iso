# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    packaging_plan_ids = fields.One2many(
        'amunet.packaging.plan',
        'production_id',
        string='Cantidad de planes de empaque',
    )
    packaging_plan_count = fields.Integer(
        string='Planes de empaque',
        compute='_compute_packaging_plan_count',
    )

    amunet_packaging_plan_approved = fields.Boolean(
        string='Plan de presentacion aprobado',
        compute='_compute_amunet_packaging_plan_approved',
        store=True,
    )

    def _compute_packaging_plan_count(self):
        for rec in self:
            rec.packaging_plan_count = len(rec.packaging_plan_ids)

    @api.depends('packaging_plan_ids.state')
    def _compute_amunet_packaging_plan_approved(self):
        for rec in self:
            rec.amunet_packaging_plan_approved = any(
                p.state in ('approved', 'done') for p in rec.packaging_plan_ids
            )

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
        self._amunet_check_packaging_plan_prerequisites()
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

    def _amunet_check_packaging_plan_prerequisites(self):
        self.ensure_one()
        missing = []
        if not self.amunet_expiration_text:
            missing.append(_('Caducidad'))
        if not self.date_start:
            missing.append(_('Fecha de inicio programada'))
        if not self.bom_id:
            missing.append(_('Lista de materiales (BoM)'))
        if not self.product_qty or self.product_qty <= 0:
            missing.append(_('Cantidad a producir'))
        if missing:
            raise UserError(_(
                'Para planear la presentacion de la orden %(mo)s, primero '
                'completa la informacion del encabezado de la orden: %(list)s.\n\n'
                'Cierra esta ventana, llena los campos en la orden y vuelve '
                'a pulsar "Planear presentacion".'
            ) % {'mo': self.name, 'list': ', '.join(missing)})

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
        """Gate de Amunet: no permitir confirmar la MO sin un plan de
        presentacion APROBADO (o cerrado). El plan define las
        presentaciones a fabricar y por tanto la cantidad de empaque
        secundario que debe surtir almacen.

        Soluciones internas se exceptuan (no se empacan en
        presentaciones secundarias).
        """
        for prod in self:
            # Soluciones no llevan plan de presentacion
            if getattr(prod, 'amunet_is_solution_product', False):
                continue
            aprobados = prod.packaging_plan_ids.filtered(
                lambda p: p.state in ('approved', 'done')
            )
            if not aprobados:
                raise UserError(_(
                    'Antes de confirmar la orden %(mo)s, aprueba un '
                    'plan de presentacion. El plan define las '
                    'presentaciones a fabricar y cuanta caja/etiqueta '
                    'debe surtir almacen.\n\n'
                    'Pulsa el boton "Planear presentación" para '
                    'crearlo, genera la sugerencia, ajusta si es '
                    'necesario y aprueba antes de confirmar.'
                ) % {'mo': prod.name})
        return super().action_confirm()
