# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import AccessError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def write(self, vals):
        # Solo bloquea si el empleado YA tiene una cuenta bancaria registrada.
        # Para empleados nuevos (sin cuenta) se permite capturar la CLABE directo.
        if 'bank_account_ids' in vals and not self.env.context.get('nomina_approved') and not self.env.su:
            for rec in self:
                if rec.bank_account_ids:
                    raise AccessError(_(
                        "La cuenta bancaria solo puede cambiarse mediante una "
                        "Solicitud de cambio de cuenta bancaria APROBADA "
                        "(Control de Nómina → Cambios de cuenta bancaria)."
                    ))
        return super().write(vals)
