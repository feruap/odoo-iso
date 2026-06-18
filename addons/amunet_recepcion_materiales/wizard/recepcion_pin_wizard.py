# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError


class RecepcionPinWizard(models.TransientModel):
    _name = 'amunet.recepcion.pin.wizard'
    _description = 'Firma electrónica para validar recepción de materiales'

    picking_id = fields.Many2one('stock.picking', required=True)
    pin = fields.Char(string='PIN de firma')

    def action_confirmar(self):
        self.ensure_one()
        if not self.pin:
            raise UserError(_('Escribe tu PIN de firma para continuar.'))
        pin_rec = self.env['amunet.quality.signature.pin'].sudo().search(
            [('user_id', '=', self.env.user.id)], limit=1)
        if not pin_rec:
            raise UserError(_(
                'No tienes un PIN de firma configurado. '
                'Solicítalo a Calidad.'
            ))
        if not pin_rec.check_pin(self.pin):
            raise ValidationError(_('PIN incorrecto. Intenta de nuevo.'))
        self.picking_id.amunet_receptor_id = self.env.user.id
        self.pin = False
        return self.picking_id.with_context(_skip_pin_wizard=True).button_validate()
