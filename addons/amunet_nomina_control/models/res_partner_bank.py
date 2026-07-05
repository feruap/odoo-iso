# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import AccessError, ValidationError


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    def _is_employee_account(self):
        partners = self.mapped("partner_id")
        if not partners:
            return False
        emp = self.env["hr.employee"].sudo().search_count([("work_contact_id", "in", partners.ids)])
        return bool(emp)

    def write(self, vals):
        if "acc_number" in vals and not self.env.context.get("nomina_approved") and not self.env.su:
            if self._is_employee_account():
                raise AccessError(_(
                    "El numero de cuenta de un empleado solo puede cambiarse mediante una "
                    "Solicitud de cambio de cuenta bancaria APROBADA (control anti-fraude)."))
        return super().write(vals)

    @api.constrains("acc_number")
    def _check_clabe_duplicada(self):
        for rec in self:
            if rec.acc_number and rec._is_employee_account():
                dup = self.sudo().search([
                    ("acc_number", "=", rec.acc_number),
                    ("id", "!=", rec.id),
                ], limit=1)
                if dup:
                    raise ValidationError(_(
                        "CLABE duplicada: la cuenta %s ya esta asignada a otro registro. "
                        "Posible riesgo de fraude.") % rec.acc_number)
