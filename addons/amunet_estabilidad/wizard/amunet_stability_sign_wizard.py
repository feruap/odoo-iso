# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError


class AmunetStabilitySignWizard(models.TransientModel):
    _name = 'amunet.stability.sign.wizard'
    _description = 'Asistente de firma de estudio de estabilidad'

    study_id = fields.Many2one('amunet.stability.study', required=True)
    role = fields.Selection([
        ('protocolo', 'Aprobar protocolo'),
        ('revisa', 'Revisó informe final'),
        ('aprueba', 'Aprobó informe final'),
    ], string='Acción', required=True, default='protocolo')
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
        if self.role == 'protocolo':
            self.study_id._do_approve_protocol()
        else:
            self.study_id._do_sign_final(self.role)
        self.pin = False
        return {'type': 'ir.actions.act_window_close'}
