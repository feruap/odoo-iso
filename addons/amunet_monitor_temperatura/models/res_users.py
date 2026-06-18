# -*- coding: utf-8 -*-
from odoo import models, fields, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    def amunet_temp_my_capture_area_ids(self):
        """Areas donde el usuario actual puede capturar (segun su
        departamento y el de los hijos si el area es de pool).
        Los usuarios de Configuracion (Mery, Fernando) ven TODAS."""
        self.ensure_one()
        areas = self.env['amunet.temp.area'].sudo().search([('active', '=', True)])
        if self.has_group('amunet_monitor_temperatura.group_temp_manager'):
            return areas
        return areas.filtered(lambda a: self in a._amunet_capturer_users())

    def amunet_temp_my_supervise_area_ids(self):
        """Areas que el usuario actual supervisa (puesto Supervisor).
        Los usuarios de Configuracion (Mery, Fernando) ven TODAS."""
        self.ensure_one()
        areas = self.env['amunet.temp.area'].sudo().search([('active', '=', True)])
        if self.has_group('amunet_monitor_temperatura.group_temp_manager'):
            return areas
        return areas.filtered(lambda a: self == a._amunet_supervisor_user())

    # ------------------------------------------------------------------
    # Acciones (construidas en Python; las llaman las ir.actions.server)
    # ------------------------------------------------------------------
    def amunet_temp_action_capture_today(self):
        self.ensure_one()
        my = self.amunet_temp_my_capture_area_ids()
        today = fields.Date.context_today(self)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Captura de hoy'),
            'res_model': 'amunet.temp.reading',
            'domain': [('area_id', 'in', my.ids), ('date', '=', today)],
            'views': [
                (self.env.ref('amunet_monitor_temperatura.view_amunet_temp_reading_kanban').id, 'kanban'),
                (self.env.ref('amunet_monitor_temperatura.view_amunet_temp_reading_list').id, 'list'),
                (self.env.ref('amunet_monitor_temperatura.view_amunet_temp_reading_form').id, 'form'),
            ],
            'context': {'search_default_f_today': 1},
            'help': '<p class="o_view_nocontent_smiley_face">Sin lecturas pendientes hoy</p>',
        }

    def amunet_temp_action_historico(self):
        self.ensure_one()
        my = (self.amunet_temp_my_capture_area_ids()
              | self.amunet_temp_my_supervise_area_ids())
        ctx = dict(self.env.context)
        if my:
            ctx['default_area_id'] = my[0].id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Historico y tendencia (grafica de control)'),
            'res_model': 'amunet.temp.chart.wizard',
            'view_mode': 'form',
            'target': 'current',
            'context': ctx,
        }

    def amunet_temp_action_supervise(self):
        self.ensure_one()
        my = self.amunet_temp_my_supervise_area_ids()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cierre diario'),
            'res_model': 'amunet.temp.daysignoff',
            'domain': [('area_id', 'in', my.ids)],
            'views': [
                (self.env.ref('amunet_monitor_temperatura.view_amunet_temp_daysignoff_kanban').id, 'kanban'),
                (self.env.ref('amunet_monitor_temperatura.view_amunet_temp_daysignoff_list').id, 'list'),
            ],
            'help': '<p class="o_view_nocontent_smiley_face">No supervisas areas o no hay dias por firmar</p>',
        }
