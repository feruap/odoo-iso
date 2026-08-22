# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AmunetBitacoraSignWizard(models.TransientModel):
    _name = 'amunet.bitacora.sign.wizard'
    _description = 'Asistente de firma de bitácora'

    entry_id = fields.Many2one('amunet.bitacora.entry', required=True)
    role = fields.Selection([
        ('captured', 'Capturó'),
        ('reviewed', 'Revisó'),
        ('approved', 'Aprobó'),
    ], string='Significado de la firma', default='captured', required=True)
    pin = fields.Char(string='PIN de firma', required=True)
    deviation_note = fields.Text(string='Nota de desviación (si aplica)')

    def action_sign(self):
        self.ensure_one()
        pin_rec = self.env['amunet.quality.signature.pin'].sudo().search(
            [('user_id', '=', self.env.user.id)], limit=1)
        if not pin_rec:
            raise UserError(_('No tienes un PIN de firma configurado. Solicítalo a Calidad.'))
        if not pin_rec.check_pin(self.pin):
            raise ValidationError(_('PIN incorrecto.'))
        if self.deviation_note:
            self.entry_id.with_context(_bitacora_internal=True).deviation_note = self.deviation_note
        self.entry_id._do_sign(self.role)
        self.pin = False
        return {'type': 'ir.actions.act_window_close'}
