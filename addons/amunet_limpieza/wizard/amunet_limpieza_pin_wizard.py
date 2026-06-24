# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AmunetLimpiezaPinWizard(models.TransientModel):
    _name = 'amunet.limpieza.pin.wizard'
    _description = 'Confirmacion de limpieza / supervision con PIN'

    tarea_id = fields.Many2one('amunet.limpieza.tarea', required=True, readonly=True)
    mode = fields.Selection([
        ('realizada', 'Registrar limpieza'),
        ('supervision', 'Firmar supervision'),
    ], required=True, readonly=True)
    area_name = fields.Char(related='tarea_id.area_id.name', string='Area', readonly=True)
    surface = fields.Selection(related='tarea_id.surface', string='Que se limpia', readonly=True)
    sanitizer = fields.Char(related='tarea_id.sanitizer', string='Sanitizante', readonly=True)
    pin = fields.Char(string='PIN', required=True)

    def action_confirm(self):
        self.ensure_one()
        self._amunet_validate_pin()
        if self.mode == 'realizada':
            self.tarea_id._apply_realizada()
        else:
            self.tarea_id._apply_supervision()
        return {'type': 'ir.actions.act_window_close'}

    def _amunet_validate_pin(self):
        """Valida el PIN contra amunet.quality.signature.pin (mismo sistema de
        firmas que los demas modulos), con respaldo al PIN de empleado."""
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
