# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class AmunetTempSignoffWizard(models.TransientModel):
    _name = 'amunet.temp.signoff.wizard'
    _description = 'Firma de cierre de desviacion / dia (con PIN)'

    mode = fields.Selection([
        ('deviation', 'Cerrar desviacion'),
        ('day', 'Firmar dia'),
    ], required=True)
    reading_id = fields.Many2one('amunet.temp.reading', readonly=True)
    daysignoff_id = fields.Many2one('amunet.temp.daysignoff', readonly=True)
    info = fields.Char(string='Resumen', compute='_compute_info')
    deviation_action = fields.Text(string='Accion tomada')
    pin = fields.Char(string='PIN', required=True)

    def _compute_info(self):
        for w in self:
            if w.mode == 'deviation' and w.reading_id:
                w.info = _('%s - %s: %.1f C / %.1f %%HR (fuera de rango)') % (
                    w.reading_id.area_id.name, w.reading_id.scheduled_label,
                    w.reading_id.temp_value, w.reading_id.hum_value)
            elif w.mode == 'day' and w.daysignoff_id:
                w.info = _('Firmar el dia %s de %s') % (
                    w.daysignoff_id.date, w.daysignoff_id.area_id.name)
            else:
                w.info = ''

    def _check_pin(self):
        """Valida el PIN contra el sistema de firmas (amunet.quality.signature.pin),
        el mismo que usan los demas modulos; con respaldo al PIN de empleado."""
        user = self.env.user
        plain = (self.pin or '').strip()
        if not plain:
            raise UserError(_('Captura tu PIN.'))
        pin_rec = self.env['amunet.quality.signature.pin'].sudo().search(
            [('user_id', '=', user.id)], limit=1)
        if pin_rec and pin_rec.check_pin(plain):
            return
        emp = user.employee_id
        if emp and emp.pin and plain == emp.pin.strip():
            return
        raise UserError(_('PIN incorrecto.'))

    def action_confirm(self):
        self.ensure_one()
        self._check_pin()
        if self.mode == 'deviation':
            if not self.deviation_action:
                raise UserError(_('Escribe la accion tomada antes de cerrar la desviacion.'))
            if not self.reading_id.area_id.amunet_user_is_supervisor():
                raise UserError(_('Solo el supervisor del area puede cerrar la desviacion.'))
            self.reading_id._apply_close_deviation(self.deviation_action)
        else:
            if not self.daysignoff_id.area_id.amunet_user_is_supervisor():
                raise UserError(_('Solo el supervisor del area puede firmar el dia.'))
            self.daysignoff_id._apply_sign()
        return {'type': 'ir.actions.act_window_close'}
