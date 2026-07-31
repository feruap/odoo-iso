# -*- coding: utf-8 -*-
import time
import logging
from odoo import fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AmunetCCRechazoWizard(models.TransientModel):
    _name = 'amunet.cc.rechazo.wizard'
    _description = 'Rechazo con firma electrónica'

    cc_id      = fields.Many2one('amunet.cc.general', required=True, readonly=True)
    motivo     = fields.Text(string='Motivo del rechazo', required=True)
    password   = fields.Char(string='Contraseña / PIN', required=True)

    def _validate_credentials(self, password):
        user = self.env.user
        pin_record = self.env['amunet.quality.signature.pin'].search(
            [('user_id', '=', user.id)], limit=1)
        if pin_record and pin_record.check_pin(password):
            return True
        try:
            uid = self.env['res.users'].authenticate(
                {'type': 'password', 'db': self.env.cr.dbname,
                 'login': user.login, 'password': password},
                {'interactive': True})
            return bool(uid)
        except Exception:
            return False

    def action_confirmar(self):
        self.ensure_one()
        if not self._validate_credentials(self.password):
            raise ValidationError(_('La contraseña o PIN es incorrecto.'))
        cc = self.cc_id
        cc.write({
            'state': 'rechazado',
            'motivo_rechazo': self.motivo,
            'firma_aprobo_id': self.env.user.id,
            'fecha_aprobo': fields.Datetime.now(),
            'vb_aprobo': 'no',
        })
        cc._message_log(
            body=_('<p><b>%s</b> rechazó el control de cambios.<br/>Motivo: %s</p>')
            % (self.env.user.name, self.motivo))
        self.env['amunet.quality.audit.log'].sudo().create({
            'model_name': cc._name,
            'res_id': cc.id,
            'res_name': cc.display_name,
            'user_id': self.env.user.id,
            'field_name': 'electronic_signature',
            'field_description': _('Rechazo del cambio'),
            'old_value': 'pendiente',
            'new_value': 'RECHAZADO',
            'justification': self.motivo,
        })
        return {'type': 'ir.actions.act_window_close'}
