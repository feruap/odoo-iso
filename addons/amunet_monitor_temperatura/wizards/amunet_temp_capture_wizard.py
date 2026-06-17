# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AmunetTempCaptureWizard(models.TransientModel):
    _name = 'amunet.temp.capture.wizard'
    _description = 'Captura de temperatura (con PIN)'

    reading_id = fields.Many2one('amunet.temp.reading', required=True, readonly=True)
    area_name = fields.Char(related='reading_id.area_id.name', string='Area', readonly=True)
    scheduled_label = fields.Char(related='reading_id.scheduled_label', string='Turno', readonly=True)
    temp_min = fields.Float(related='reading_id.temp_min', readonly=True)
    temp_max = fields.Float(related='reading_id.temp_max', readonly=True)
    hum_min = fields.Float(related='reading_id.hum_min', readonly=True)
    hum_max = fields.Float(related='reading_id.hum_max', readonly=True)
    hum_required = fields.Boolean(related='reading_id.hum_required', readonly=True)
    instrument_name = fields.Char(related='reading_id.instrument_name', readonly=True)

    temp_value = fields.Float(string='Temperatura (C)', required=True)
    hum_value = fields.Float(string='Humedad (%HR)')
    observation = fields.Text(string='Observacion')
    pin = fields.Char(string='PIN', required=True)

    def action_confirm(self):
        self.ensure_one()
        reading = self.reading_id
        if reading.state not in ('pending', 'missed'):
            raise UserError(_('Esta lectura ya fue capturada.'))
        if not reading.area_id.amunet_user_can_capture():
            raise UserError(_('No perteneces al area "%s".') % reading.area_id.name)
        reading._amunet_check_capture_window()
        self._amunet_validate_pin()
        if self.hum_required and not self.hum_value and self.hum_value != 0.0:
            raise UserError(_('Captura la humedad (es obligatoria en esta area).'))
        reading._apply_capture(self.temp_value, self.hum_value, self.observation)
        return {'type': 'ir.actions.act_window_close'}

    def _amunet_validate_pin(self):
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
