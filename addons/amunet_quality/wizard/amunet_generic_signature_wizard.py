# -*- coding: utf-8 -*-
import logging
import time

from odoo import api, fields, models, _
from odoo.exceptions import AccessDenied, ValidationError

_logger = logging.getLogger(__name__)


class AmunetGenericSignatureWizard(models.TransientModel):
    _name = 'amunet.generic.signature.wizard'
    _description = 'Firma Electronica Amunet'

    res_model = fields.Char(string='Modelo', required=True, readonly=True)
    res_id = fields.Integer(string='Registro', required=True, readonly=True)
    method_name = fields.Char(string='Accion interna', required=True, readonly=True)
    signature_type = fields.Char(string='Tipo de firma', required=True, readonly=True)
    reason = fields.Text(string='Motivo', readonly=True)
    password = fields.Char(
        string='Contrasena / PIN',
        required=True,
        help='Ingrese su contrasena de Odoo o PIN de firma.',
    )

    @api.model
    def open_for(self, record, method_name, signature_type, reason=None):
        record.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Firma electronica'),
            'res_model': self._name,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': record._name,
                'default_res_id': record.id,
                'default_method_name': method_name,
                'default_signature_type': signature_type,
                'default_reason': reason or '',
            },
        }

    def _validate_credentials(self, password_or_pin):
        user = self.env.user
        pin_record = self.env['amunet.quality.signature.pin'].search([
            ('user_id', '=', user.id),
        ], limit=1)
        if pin_record and pin_record.check_pin(password_or_pin):
            return True
        return self._validate_user_password(password_or_pin)

    def _validate_user_password(self, password):
        if not password:
            return False
        user = self.env.user
        credentials = {
            'type': 'password',
            'db': self.env.cr.dbname,
            'login': user.login,
            'password': password,
        }
        try:
            uid = self.env['res.users'].authenticate(
                credentials, {'interactive': True})
            return bool(uid)
        except Exception:
            _logger.info(
                'Fallo autenticando firma generica para user=%s',
                user.login,
                exc_info=True,
            )
            return False

    def _target_record(self):
        self.ensure_one()
        if not self.res_model or not self.res_id:
            raise ValidationError(_('La firma no tiene registro destino.'))
        record = self.env[self.res_model].browse(self.res_id).exists()
        if not record:
            raise ValidationError(_('El registro destino ya no existe.'))
        record.ensure_one()
        return record

    def _check_method_allowed(self, record):
        allowed_getter = getattr(record, '_amunet_signature_allowed_methods', None)
        if not allowed_getter:
            raise AccessDenied(_('Este registro no admite firma electronica.'))
        allowed = allowed_getter()
        if self.method_name not in allowed:
            raise AccessDenied(_('Accion de firma no autorizada.'))
        return allowed[self.method_name]

    def _log_signature_event(self, record, success=True):
        status = 'EXITOSA' if success else 'FALLIDA'
        self.env['amunet.quality.audit.log'].sudo().create({
            'model_name': record._name if record else (self.res_model or 'N/A'),
            'res_id': record.id if record else (self.res_id or 0),
            'res_name': record.display_name if record else 'WIZARD',
            'user_id': self.env.user.id,
            'field_name': 'electronic_signature',
            'field_description': self.signature_type,
            'old_value': 'N/A',
            'new_value': status,
            'justification': self.reason or self.signature_type,
        })

    def action_confirm_signature(self):
        started_at = time.perf_counter()
        timings = {}

        def mark(step, step_started_at):
            timings[step] = time.perf_counter() - step_started_at
            return time.perf_counter()

        self.ensure_one()
        step_started_at = time.perf_counter()
        record = self._target_record()
        step_started_at = mark('target_record', step_started_at)
        label = self._check_method_allowed(record)
        step_started_at = mark('method_allowed', step_started_at)
        if not self._validate_credentials(self.password):
            step_started_at = mark('credentials_failed', step_started_at)
            self._log_signature_event(record, success=False)
            mark('audit_failed', step_started_at)
            _logger.warning(
                'AMUNET_SIGNATURE_TIMING status=failed model=%s res_id=%s method=%s total=%.3fs details=%s',
                record._name,
                record.id,
                self.method_name,
                time.perf_counter() - started_at,
                ','.join('%s=%.3fs' % (key, value) for key, value in timings.items()),
            )
            raise ValidationError(_('La contrasena o PIN es incorrecto.'))
        step_started_at = mark('credentials_ok', step_started_at)

        method = getattr(record, self.method_name)
        result = method()
        step_started_at = mark('target_method', step_started_at)
        self.signature_type = self.signature_type or label
        step_started_at = mark('signature_type_write', step_started_at)
        self._log_signature_event(record, success=True)
        mark('audit_success', step_started_at)
        _logger.warning(
            'AMUNET_SIGNATURE_TIMING status=success model=%s res_id=%s method=%s total=%.3fs details=%s',
            record._name,
            record.id,
            self.method_name,
            time.perf_counter() - started_at,
            ','.join('%s=%.3fs' % (key, value) for key, value in timings.items()),
        )
        return result or {'type': 'ir.actions.act_window_close'}
