from odoo import models

CODIGOS_RETENCION = {'ISR', 'IMSS'}


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _compute_payslip_line(self, rule, localdict, lines_dict):
        emp = localdict.get('employee')
        if rule.code in CODIGOS_RETENCION and emp and emp.exento_retenciones:
            valores_cero = {'name': rule.name, 'quantity': 1.0, 'rate': 100.0, 'amount': 0.0}
            key = (rule.code or 'id' + str(rule.id)) + '-' + str(localdict['contract'].id)
            return self._get_lines_dict(rule, localdict, lines_dict, key, valores_cero, 0.0)
        return super()._compute_payslip_line(rule, localdict, lines_dict)
