# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import AccessError


class HrVersion(models.Model):
    _inherit = "hr.version"

    def write(self, vals):
        if "wage" in vals and not self.env.context.get("nomina_approved") and not self.env.su:
            for rec in self:
                if rec.employee_id and rec.wage != vals.get("wage"):
                    raise AccessError(_(
                        "El sueldo solo puede cambiarse mediante una Solicitud de cambio de "
                        "sueldo APROBADA (control anti-fraude)."))
        return super().write(vals)
