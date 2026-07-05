# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, _
from odoo.exceptions import AccessError, ValidationError


class HrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"

    nomina_alertas = fields.Text("Alertas de control anti-fraude", readonly=True)

    def _validar_nomina(self, block=False):
        for run in self:
            criticas, avisos, vistas = [], [], {}
            limite = fields.Datetime.now() - timedelta(days=3)
            for slip in run.slip_ids:
                emp = slip.employee_id
                if not emp.sudo().nomina_aprobado:
                    criticas.append("%s: empleado NO aprobado para nomina" % emp.name)
                wage = emp.current_version_id.wage or 0.0
                net = sum(slip.line_ids.filtered(lambda l: l.code == "NET").mapped("total"))
                if wage and net > wage * 1.3:
                    avisos.append("%s: neto %.2f alto vs sueldo %.2f (revisar)" % (emp.name, net, wage))
                rec = self.env["amunet.bank.change.request"].sudo().search_count([
                    ("employee_id", "=", emp.id), ("state", "=", "aprobada"),
                    ("approved_date", ">=", limite)])
                if rec:
                    avisos.append("%s: cuenta bancaria cambiada en los ultimos 3 dias (revisar)" % emp.name)
                acct = emp.primary_bank_account_id.acc_number
                if acct:
                    if acct in vistas and vistas[acct] != emp.id:
                        criticas.append("CLABE %s repetida en el lote" % acct)
                    vistas[acct] = emp.id
            run.nomina_alertas = "\n".join(criticas + avisos) or "Sin alertas."
            if block and criticas:
                raise ValidationError(_("No se puede autorizar el lote (control anti-fraude):\n%s") % "\n".join(criticas))
        return True

    def action_validar_nomina(self):
        self._validar_nomina(block=False)
        return True

    def close_payslip_run(self):
        if not self.env.user.has_group("amunet_nomina_control.group_nomina_autorizador"):
            raise AccessError(_("Solo un Autorizador puede autorizar/cerrar el lote de nomina."))
        self._validar_nomina(block=True)
        return super().close_payslip_run()
