# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import ValidationError


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def compute_sheet(self):
        for slip in self:
            emp = slip.employee_id
            if emp and not emp.sudo().nomina_aprobado:
                raise ValidationError(_(
                    "El empleado '%s' no esta APROBADO para nomina. "
                    "Un Autorizador debe aprobar el alta antes de generar su recibo (control anti-fraude).")
                    % emp.name)
        return super().compute_sheet()
