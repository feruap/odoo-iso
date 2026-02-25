# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from passlib.context import CryptContext
import logging

_logger = logging.getLogger(__name__)

class AmunetQualitySignaturePin(models.Model):
    """
    Modelo independiente para almacenar PINs de firma electrónica.
    """
    _name = 'amunet.quality.signature.pin'
    _description = 'PIN de Firma de Calidad'
    _rec_name = 'user_id'

    user_id = fields.Many2one('res.users', string='Usuario', required=True, index=True)
    pin = fields.Char(string='PIN (Hashed)', required=True, help='PIN de firma almacenado de forma segura')

    _sql_constraints = [
        ('user_id_uniq', 'unique(user_id)', 'El usuario ya tiene un PIN asignado.')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """Asegurar que el PIN se hashee al crear, solo si no es un hash."""
        _logger.info("CREATING PIN: %s", vals_list)
        pwd_context = CryptContext(schemes=["pbkdf2_sha512"], deprecated="auto")
        
        # Handle both single dict and list of dicts for safety
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if isinstance(vals, dict) and vals.get('pin'):
                # Detección más robusta: si empieza por $ y tiene longitud de hash, no re-hashear
                pin_val = vals['pin']
                if not (pin_val.startswith('$') and len(pin_val) > 20):
                    vals['pin'] = pwd_context.hash(pin_val)
        
        return super(AmunetQualitySignaturePin, self).create(vals_list)

    def write(self, vals):
        """Asegurar que el PIN se hashee al modificar, evitando doble hasheo."""
        _logger.info("WRITING PIN: %s", vals)
        if vals.get('pin'):
            pwd_context = CryptContext(schemes=["pbkdf2_sha512"], deprecated="auto")
            # Detección más robusta para evitar re-hashear valores que ya parecen hashes
            pin_val = vals.get('pin')
            if not (pin_val.startswith('$') and len(pin_val) > 20):
                vals['pin'] = pwd_context.hash(pin_val)
        return super(AmunetQualitySignaturePin, self).write(vals)

    def _set_pin(self, plain_pin):
        """Hashea y guarda el PIN."""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["pbkdf2_sha512"], deprecated="auto")
        self.pin = pwd_context.hash(plain_pin)

    def check_pin(self, plain_pin):
        """Verifica el PIN contra el hash con fallback a texto plano para migración."""
        if not self.pin or not plain_pin:
            return False
            
        # 1. Intentar comparación exacta (Fallback para PINs no hasheados aún)
        if self.pin == str(plain_pin):
            _logger.warning("PIN match via plain text for user ID %s. Auto-hashing for security.", self.user_id.id)
            self.sudo()._set_pin(str(plain_pin))
            return True

        # 2. Verificación estándar de Hash
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["pbkdf2_sha512"], deprecated="auto")
        try:
            return pwd_context.verify(str(plain_pin), self.pin)
        except Exception as e:
            _logger.info("PIN Context verify error (likely not a hash): %s", str(e))
            return False
