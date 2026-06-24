# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from .amunet_limpieza_item import SURFACE_SEL, FREQ_SEL


class AmunetLimpiezaTarea(models.Model):
    _name = 'amunet.limpieza.tarea'
    _description = 'Tarea de limpieza (registro por area, dia y superficie)'
    _inherit = ['mail.thread']
    _order = 'date desc, area_id, surface'
    _rec_name = 'display_name'

    item_id = fields.Many2one('amunet.limpieza.item', string='Item', ondelete='set null')
    area_id = fields.Many2one(
        'amunet.temp.area', string='Area', required=True, ondelete='restrict', index=True)
    surface = fields.Selection(SURFACE_SEL, string='Que se limpia', required=True)
    frequency = fields.Selection(FREQ_SEL, string='Frecuencia')
    date = fields.Date(string='Fecha', required=True, index=True,
                       default=fields.Date.context_today)
    sanitizer = fields.Char(string='Sanitizante (de la semana)', readonly=True)
    display_name = fields.Char(compute='_compute_display_name')

    state = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('realizada', 'Realizada'),
        ('omitida', 'Omitida'),
    ], string='Estado', default='pendiente', required=True, index=True, tracking=True)

    realizado_by = fields.Many2one('res.users', string='Limpio', readonly=True, tracking=True)
    realizado_at = fields.Datetime(string='Limpiado el', readonly=True)
    supervisado_by = fields.Many2one('res.users', string='Superviso (firma)', readonly=True, tracking=True)
    supervisado_at = fields.Datetime(string='Supervisado el', readonly=True)

    observacion = fields.Text(string='Observacion')
    omitida_motivo = fields.Text(string='Motivo de omision (lo marca el supervisor)')

    @api.depends('area_id', 'surface', 'date')
    def _compute_display_name(self):
        labels = dict(SURFACE_SEL)
        for r in self:
            r.display_name = '%s - %s - %s' % (
                r.area_id.name or '', labels.get(r.surface, ''), r.date or '')

    # ------------------------------------------------------------------
    # Rotacion de sanitizante: alterna cada lunes (por numero de semana ISO)
    # ------------------------------------------------------------------
    @api.model
    def _amunet_sanitizer_for_date(self, date, rule):
        if rule == 'alcohol':
            return 'Alcohol 70%'
        week = date.isocalendar()[1]
        return 'Cloro 0.1%' if (week % 2 == 0) else 'Sales cuaternarias 0.05%'

    # ------------------------------------------------------------------
    # Cron: generar tareas del dia y marcar omitidas las vencidas
    # ------------------------------------------------------------------
    @api.model
    def _cron_generar_y_marcar(self):
        today = fields.Date.context_today(self)
        Item = self.env['amunet.limpieza.item'].sudo().search([('active', '=', True)])
        for item in Item:
            if item.frequency == 'diario':
                due = True
            elif item.frequency == 'semanal':
                due = today.weekday() == (item.weekday or 5)
            elif item.frequency == 'mensual':
                due = today.day == 1
            else:
                due = False
            if not due:
                continue
            exists = self.sudo().search([
                ('item_id', '=', item.id), ('date', '=', today)], limit=1)
            if not exists:
                self.sudo().create({
                    'item_id': item.id,
                    'area_id': item.area_id.id,
                    'surface': item.surface,
                    'frequency': item.frequency,
                    'date': today,
                    'sanitizer': self._amunet_sanitizer_for_date(today, item.sanitizer_rule),
                })
        # Vencidas pendientes -> omitidas
        self.sudo().search([
            ('date', '<', today), ('state', '=', 'pendiente')]).write({'state': 'omitida'})
        return True

    # ------------------------------------------------------------------
    # Acciones: Limpie (responsable) y Firmar supervision (supervisor)
    # ------------------------------------------------------------------
    def action_open_limpie(self):
        self.ensure_one()
        if self.state == 'realizada':
            raise UserError(_('Esta limpieza ya fue registrada.'))
        return self._amunet_open_pin_wizard('realizada', _('Confirmar limpieza'))

    def action_open_firmar(self):
        self.ensure_one()
        if self.state != 'realizada':
            raise UserError(_('Primero el responsable debe registrar la limpieza.'))
        if self.supervisado_by:
            raise UserError(_('Esta limpieza ya fue firmada por el supervisor.'))
        if not self.area_id.amunet_user_is_supervisor():
            raise UserError(_(
                'Solo el supervisor del area "%s" puede firmar la supervision.'
            ) % self.area_id.name)
        return self._amunet_open_pin_wizard('supervision', _('Firmar supervision'))

    def _amunet_open_pin_wizard(self, mode, title):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': title,
            'res_model': 'amunet.limpieza.pin.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_tarea_id': self.id, 'default_mode': mode},
        }

    def _apply_realizada(self):
        self.ensure_one()
        self.write({
            'state': 'realizada',
            'realizado_by': self.env.user.id,
            'realizado_at': fields.Datetime.now(),
        })
        self.message_post(body=_('Limpieza registrada por %s. Sanitizante: %s.') % (
            self.env.user.name, self.sanitizer or '-'))

    def _apply_supervision(self):
        self.ensure_one()
        self.write({
            'supervisado_by': self.env.user.id,
            'supervisado_at': fields.Datetime.now(),
        })
        self.message_post(body=_('Supervision firmada por %s.') % self.env.user.name)
