import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AmunetActaAsistenciaWizard(models.TransientModel):
    _name = 'amunet.acta.asistencia.wizard'
    _description = 'Registrar asistencia con PIN'

    acta_id = fields.Many2one('amunet.acta.auditoria', required=True, readonly=True)
    seccion = fields.Selection([
        ('apertura', 'Apertura'),
        ('cierre', 'Cierre'),
    ], required=True, readonly=True)
    usuario_nombre = fields.Char(string='Registrando asistencia de', readonly=True)
    password = fields.Char(string='PIN / Contraseña', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res['usuario_nombre'] = self.env.user.name
        return res

    def _validar_credenciales(self, password):
        user = self.env.user
        pin_record = self.env['amunet.quality.signature.pin'].sudo().search(
            [('user_id', '=', user.id)], limit=1
        )
        if pin_record and pin_record.check_pin(password):
            return True
        try:
            credentials = {
                'type': 'password',
                'db': self.env.cr.dbname,
                'login': user.login,
                'password': password,
            }
            uid = self.env['res.users'].authenticate(credentials, {'interactive': True})
            return bool(uid)
        except Exception:
            _logger.info('Fallo autenticando asistencia para user=%s', user.login, exc_info=True)
            return False

    def action_confirmar(self):
        self.ensure_one()
        user = self.env.user

        if not self._validar_credenciales(self.password):
            raise ValidationError(_('El PIN o contraseña es incorrecto.'))

        acta = self.acta_id
        if self.seccion == 'apertura':
            ya = user.id in acta.apertura_asistente_ids.mapped('user_id').ids
        else:
            ya = user.id in acta.cierre_asistente_ids.mapped('user_id').ids

        if ya:
            seccion_label = dict(self._fields['seccion'].selection)[self.seccion].lower()
            raise ValidationError(_(
                'Ya registraste tu asistencia en la reunión de %s.'
            ) % seccion_label)

        self.env['amunet.acta.asistente'].sudo().create({
            'acta_id': acta.id,
            'seccion': self.seccion,
            'user_id': user.id,
            'fecha': fields.Date.today(),
        })

        return {'type': 'ir.actions.act_window_close'}
