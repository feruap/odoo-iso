# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError


class BankChangeRequest(models.Model):
    _name = "amunet.bank.change.request"
    _description = "Solicitud de cambio de cuenta bancaria"
    _order = "create_date desc"

    name = fields.Char("Folio", default="Nueva solicitud", readonly=True)
    employee_id = fields.Many2one("hr.employee", string="Empleado", required=True)
    bank_id = fields.Many2one("res.partner.bank", string="Cuenta actual")
    old_acc = fields.Char("Cuenta anterior", readonly=True)
    new_acc = fields.Char("Cuenta nueva (CLABE)", required=True)
    reason = fields.Text("Motivo del cambio")
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
            bank = False
            emp = rec.employee_id
            if emp and "primary_bank_account_id" in emp._fields:
                bank = emp.primary_bank_account_id
            rec.bank_id = bank
            rec.old_acc = bank.acc_number if bank else ""

    def _amunet_signature_allowed_methods(self):
        return {"action_approve": _("Aprobar cambio de cuenta bancaria")}

    def action_open_approve(self):
        self.ensure_one()
        if not self.env.user.has_group("amunet_nomina_control.group_nomina_autorizador"):
            raise AccessError(_("Solo un Autorizador de nomina puede aprobar."))
        if self.env.user == self.requested_by_id:
            raise AccessError(_("No puede aprobar su propia solicitud (segregacion de funciones)."))
        if self.state != "pendiente":
            raise ValidationError(_("La solicitud ya no esta pendiente."))
        return self.env["amunet.generic.signature.wizard"].open_for(
            self, "action_approve", _("Aprobacion de cambio de cuenta bancaria"), self.reason or "")

    def _check_can_approve(self):
        """Mismas reglas que el boton: se re-validan aqui porque el metodo
        final es publico (RPC) y usa sudo() para escribir en el empleado."""
        self.ensure_one()
        if not self.env.user.has_group("amunet_nomina_control.group_nomina_autorizador"):
            raise AccessError(_("Solo un Autorizador de nomina puede aprobar."))
        if self.env.user == self.requested_by_id:
            raise AccessError(_("No puede aprobar su propia solicitud (segregacion de funciones)."))
        if self.state != "pendiente":
            raise ValidationError(_("La solicitud ya no esta pendiente."))

    def action_approve(self):
        self.ensure_one()
        self._check_can_approve()
        emp = self.employee_id
        partner = (self.bank_id.partner_id if self.bank_id else False) or emp.work_contact_id
        new_bank = self.env["res.partner.bank"].sudo().with_context(nomina_approved=True).create({
            "acc_number": self.new_acc,
            "partner_id": partner.id,
        })
        emp.sudo().write({"bank_account_ids": [(6, 0, [new_bank.id])]})
        emp.sudo().salary_distribution = {
            str(new_bank.id): {"sequence": 0, "amount": 100.0, "amount_is_percentage": True}
        }
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
