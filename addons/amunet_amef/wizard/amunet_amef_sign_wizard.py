# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError


class AmunetAmefSignWizard(models.TransientModel):
    _name = 'amunet.amef.sign.wizard'
    _description = 'Asistente de firma de AMEF'

    amef_id = fields.Many2one('amunet.amef', required=True)
    role = fields.Selection([
        ('revisa', 'Revisó'),
        ('aprueba', 'Aprobó'),
    ], string='Significado de la firma', default='revisa', required=True)
    pin = fields.Char(string='PIN de firma', required=True)
    motivo = fields.Char(string='Motivo / comentario')

    def action_sign(self):
        self.ensure_one()
        pin_rec = self.env['amunet.quality.signature.pin'].sudo().search(
            [('user_id', '=', self.env.user.id)], limit=1)
        if not pin_rec:
            raise UserError(_('No tienes un PIN de firma configurado. Solicítalo a Calidad.'))
        if not pin_rec.check_pin(self.pin):
            raise ValidationError(_('PIN incorrecto.'))
        self.amef_id._do_approve(self.role)
        self.pin = False
        return {'type': 'ir.actions.act_window_close'}
