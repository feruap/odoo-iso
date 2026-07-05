# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    nomina_aprobado = fields.Boolean("Aprobado para nomina", default=False, tracking=True, groups="hr.group_hr_user")
    nomina_aprobado_por_id = fields.Many2one("res.users", "Aprobado por", readonly=True, groups="hr.group_hr_user")
    nomina_aprobado_fecha = fields.Datetime("Fecha de aprobacion", readonly=True, groups="hr.group_hr_user")

    def _amunet_signature_allowed_methods(self):
        return {"action_aprobar_nomina": _("Aprobar empleado para nomina")}

    def action_open_aprobar_nomina(self):
        self.ensure_one()
        if not self.env.user.has_group("amunet_nomina_control.group_nomina_autorizador"):
            raise AccessError(_("Solo un Autorizador puede aprobar el alta del empleado."))
        if self.env.user == self.create_uid:
            raise AccessError(_("No puede aprobar un empleado que usted mismo dio de alta (segregacion)."))
        return self.env["amunet.generic.signature.wizard"].open_for(
            self, "action_aprobar_nomina", _("Aprobacion de alta de empleado"), self.name)

    def action_aprobar_nomina(self):
        self.sudo().write({
            "nomina_aprobado": True,
            "nomina_aprobado_por_id": self.env.user.id,
            "nomina_aprobado_fecha": fields.Datetime.now(),
        })
        return True
