# -*- coding: utf-8 -*-
from odoo import models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def get_worked_day_lines(self, contracts, date_from, date_to):
        if self.struct_id and self.struct_id.code == 'FINIQUITO':
            return []
        return super().get_worked_day_lines(contracts, date_from, date_to)
