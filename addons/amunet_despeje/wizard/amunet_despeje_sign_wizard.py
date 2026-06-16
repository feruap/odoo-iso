# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError


class AmunetDespejeSignWizard(models.TransientModel):
    _name = 'amunet.despeje.sign.wizard'
    _description = 'Asistente de firma de despeje'

    despeje_id = fields.Many2one('amunet.despeje', required=True)
    pin = fields.Char(string='PIN de firma', required=True)

    def action_sign(self):
        self.ensure_one()
        pin_rec = self.env['amunet.quality.signature.pin'].sudo().search(
            [('user_id', '=', self.env.user.id)], limit=1)
        if not pin_rec:
            raise UserError(_('No tienes un PIN de firma configurado.'))
        if not pin_rec.check_pin(self.pin):
            raise ValidationError(_('PIN incorrecto.'))
        self.despeje_id._do_sign()
        self.pin = False
        return {'type': 'ir.actions.act_window_close'}
