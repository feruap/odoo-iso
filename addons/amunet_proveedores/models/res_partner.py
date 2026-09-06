# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    reevaluacion_vencida = fields.Boolean(
        string='Reevaluación vencida', compute='_compute_reevaluacion', search='_search_reevaluacion')
    dias_para_reevaluacion = fields.Integer(
        string='Días para reevaluación', compute='_compute_reevaluacion')

    @api.depends('next_audit_date')
    def _compute_reevaluacion(self):
        today = fields.Date.context_today(self)
        for p in self:
            if p.next_audit_date:
                p.dias_para_reevaluacion = (p.next_audit_date - today).days
                p.reevaluacion_vencida = p.next_audit_date < today
            else:
                p.dias_para_reevaluacion = 0
                p.reevaluacion_vencida = False

    def _search_reevaluacion(self, operator, value):
        today = fields.Date.context_today(self)
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('next_audit_date', '<', today)]
        return ['|', ('next_audit_date', '>=', today), ('next_audit_date', '=', False)]

    @api.model
    def _cron_supplier_reevaluation(self):
        """Crea una actividad para Calidad por cada proveedor con reevaluación vencida o próxima (30 días)."""
        today = fields.Date.context_today(self)
        limite = fields.Date.add(today, days=30)
        proveedores = self.search([
            ('supplier_rank', '>', 0),
            ('next_audit_date', '!=', False),
            ('next_audit_date', '<=', limite),
        ])
        manager = self.env.ref('amunet_quality.group_quality_manager', raise_if_not_found=False)
        user = self.env.user
        # Odoo 19: res.groups ya no tiene `users`; el campo es `user_ids`
        if manager and manager.user_ids:
            user = manager.user_ids[0]
        for p in proveedores:
            ya = self.env['mail.activity'].search_count([
                ('res_model', '=', 'res.partner'), ('res_id', '=', p.id),
                ('summary', 'like', 'Reevaluación de proveedor'),
            ])
            if ya:
                continue
            p.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Reevaluación de proveedor %s') % (p.name or ''),
                note=_('La próxima auditoría/reevaluación vence el %s. Programa la auditoría.') % p.next_audit_date,
                user_id=user.id,
            )
        return True
