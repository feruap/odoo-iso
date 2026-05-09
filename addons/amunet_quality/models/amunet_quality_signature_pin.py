# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError
from passlib.context import CryptContext
import logging

_logger = logging.getLogger(__name__)


class AmunetQualitySignaturePin(models.Model):
    """
    Modelo independiente para almacenar PINs de firma electronica.
    """
    _name = 'amunet.quality.signature.pin'
    _description = 'PIN de Firma de Calidad'
    _rec_name = 'user_id'

    PIN_MASK = '********'

    user_id = fields.Many2one('res.users', string='Usuario', required=True, index=True)
    pin = fields.Char(string='PIN (Hashed)', required=True, help='PIN de firma almacenado de forma segura')

    _sql_constraints = [
        ('user_id_uniq', 'unique(user_id)', 'El usuario ya tiene un PIN asignado.')
    ]

    def _is_pin_admin(self):
        return (
            self.env.su
            or self.env.user.has_group('base.group_system')
            or self.env.user.has_group('amunet_quality.group_quality_manager')
        )

    def _hash_pin_if_needed(self, pin_val):
        if not pin_val or pin_val == self.PIN_MASK:
            return pin_val
        pin_text = str(pin_val)
        if pin_text.startswith('$') and len(pin_text) > 20:
            return pin_text
        pwd_context = CryptContext(schemes=["pbkdf2_sha512"], deprecated="auto")
        return pwd_context.hash(pin_text)

    @api.model_create_multi
    def create(self, vals_list):
        """Hashear el PIN al crear sin registrar el valor en logs."""
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        protected_vals = []
        for vals in vals_list:
            vals = dict(vals)
            if not self._is_pin_admin():
                requested_user = vals.get('user_id') or self.env.user.id
                if requested_user != self.env.user.id:
                    raise AccessError(_("Solo puede crear o modificar su propio PIN de firma."))
                vals['user_id'] = self.env.user.id

            if vals.get('pin'):
                vals['pin'] = self._hash_pin_if_needed(vals['pin'])
            protected_vals.append(vals)

        return super().create(protected_vals)

    def write(self, vals):
        """Hashear el PIN al modificar sin registrar el valor en logs."""
        vals = dict(vals)
        if not self._is_pin_admin():
            if any(record.user_id != self.env.user for record in self):
                raise AccessError(_("Solo puede modificar su propio PIN de firma."))
            if 'user_id' in vals and vals['user_id'] != self.env.user.id:
                raise AccessError(_("No puede reasignar un PIN de firma a otro usuario."))

        if vals.get('pin') == self.PIN_MASK:
            vals.pop('pin')
        elif vals.get('pin'):
            vals['pin'] = self._hash_pin_if_needed(vals['pin'])
        return super().write(vals)

    def unlink(self):
        if not self._is_pin_admin():
            raise AccessError(_("Los PIN de firma solo pueden ser eliminados por un administrador de calidad."))
        return super().unlink()

    def read(self, fields=None, load='_classic_read'):
        """No exponer el hash del PIN por vistas o lecturas RPC normales."""
        values = super().read(fields=fields, load=load)
        if fields is None or 'pin' in fields:
            for record_values in values:
                if record_values.get('pin'):
                    record_values['pin'] = self.PIN_MASK
        return values

    def _set_pin(self, plain_pin):
        """Hashea y guarda el PIN."""
        self.pin = self._hash_pin_if_needed(plain_pin)

    def check_pin(self, plain_pin):
        """Verifica el PIN contra el hash con fallback a texto plano para migracion."""
        if not self.pin or not plain_pin:
            return False

        if self.pin == str(plain_pin):
            _logger.warning(
                "PIN match via plain text for user ID %s. Auto-hashing for security.",
                self.user_id.id,
            )
            self.sudo()._set_pin(str(plain_pin))
            return True

        pwd_context = CryptContext(schemes=["pbkdf2_sha512"], deprecated="auto")
        try:
            return pwd_context.verify(str(plain_pin), self.pin)
        except Exception as e:
            _logger.info("PIN Context verify error (likely not a hash): %s", str(e))
            return False
