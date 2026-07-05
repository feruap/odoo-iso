# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError


class SalaryChangeRequest(models.Model):
    _name = "amunet.salary.change.request"
    _description = "Solicitud de cambio de sueldo"
    _order = "create_date desc"

    employee_id = fields.Many2one("hr.employee", string="Empleado", required=True)
    old_wage = fields.Float("Sueldo anterior", readonly=True)
    new_wage = fields.Float("Sueldo nuevo", required=True)
    reason = fields.Text("Motivo")
    state = fields.Selection([
        ("pendiente", "Pendiente de firma"),
        ("aprobada", "Aprobada"),
        ("rechazada", "Rechazada"),
    ], default="pendiente", string="Estado", tracking=True)
    requested_by_id = fields.Many2one("res.users", string="Solicito", default=lambda s: s.env.user, readonly=True)
    approved_by_id = fields.Many2one("res.users", string="Autorizo", readonly=True)
    approved_date = fields.Datetime("Fecha autorizacion", readonly=True)

    @api.onchange("employee_id")
    def _onchange_employee(self):
        for rec in self:
            ver = rec.employee_id.current_version_id if rec.employee_id else False
            rec.old_wage = ver.wage if ver else 0.0

    def _amunet_signature_allowed_methods(self):
        return {"action_approve": _("Aprobar cambio de sueldo")}

    def action_open_approve(self):
        self.ensure_one()
        if not self.env.user.has_group("amunet_nomina_control.group_nomina_autorizador"):
            raise AccessError(_("Solo un Autorizador puede aprobar."))
        if self.env.user == self.requested_by_id:
            raise AccessError(_("No puede aprobar su propia solicitud (segregacion de funciones)."))
        if self.state != "pendiente":
            raise ValidationError(_("La solicitud ya no esta pendiente."))
        return self.env["amunet.generic.signature.wizard"].open_for(
            self, "action_approve", _("Aprobacion de cambio de sueldo"), self.reason or "")

    def action_approve(self):
        self.ensure_one()
        ver = self.employee_id.current_version_id
        ver.sudo().with_context(nomina_approved=True).write({"wage": self.new_wage})
        self.write({
            "state": "aprobada",
            "approved_by_id": self.env.user.id,
            "approved_date": fields.Datetime.now(),
        })
        return True

    def action_reject(self):
        self.ensure_one()
        if not self.env.user.has_group("amunet_nomina_control.group_nomina_autorizador"):
            raise AccessError(_("Solo un Autorizador puede rechazar."))
        self.state = "rechazada"
