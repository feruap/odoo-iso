# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import AccessError

# Único usuario humano autorizado a generar API keys (login real = email).
ALLOWED_LOGIN = 'fernando.ruiz@amunet.com.mx'


class ResUsersApikeys(models.Model):
    _inherit = 'res.users.apikeys'

    def _generate(self, scope, name, expiration_date):
        # Permitido solo para el líder del proyecto, o procesos de backend en superusuario.
        if not self.env.su and self.env.user.login != ALLOWED_LOGIN:
            raise AccessError(_(
                "Solo el líder del proyecto (fernando.ruiz) está autorizado a generar "
                "claves API. Si necesitas conectar un sistema externo, solicítalo a Fernando."))
        return super()._generate(scope, name, expiration_date)
