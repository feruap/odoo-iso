# -*- coding: utf-8 -*-

import re

from markupsafe import escape

from odoo import api, fields, models, _
from odoo.exceptions import UserError


DEMO_FVA_MISSING = {
    "PRO/VOR/02",
    "PRO/COH/01",
    "PRO/COT/01",
    "CAL/LMP/01",
    "PRO/SDM/01",
    "PRO/SEL/01",
    "CAL/CNM/03",
}


class AmunetLotDossier(models.Model):
    _name = "amunet.lot.dossier"
    _description = "Expediente digital de lote"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "write_date desc, id desc"

    name = fields.Char(compute="_compute_name", store=True, readonly=True)
    active = fields.Boolean(default=True)
    lot_id = fields.Many2one(
        "stock.lot",
        string="Lote",
        required=True,
        index=True,
        tracking=True,
        ondelete="restrict",
    )
    product_id = fields.Many2one(
        "product.product",
        string="Producto",
        related="lot_id.product_id",
        store=True,
        readonly=True,
    )
    release_state = fields.Selection(
        related="lot_id.amunet_lot_release_state",
        string="Liberacion DHR",
        store=True,
        readonly=True,
    )
    release_hash = fields.Char(
        related="lot_id.amunet_lot_release_hash",
        string="Hash DHR",
        readonly=True,
    )
    released_by_id = fields.Many2one(
        related="lot_id.amunet_lot_released_by_id",
        string="Liberado por",
        readonly=True,
    )
    released_date = fields.Datetime(
        related="lot_id.amunet_lot_released_date",
        string="Fecha liberacion",
        readonly=True,
    )
    release_snapshot = fields.Text(
        related="lot_id.amunet_lot_release_snapshot",
        string="Snapshot DHR",
        readonly=True,
    )

    production_id = fields.Many2one(
        "mrp.production",
        compute="_compute_production_id",
        string="Orden de fabricacion",
        store=True,
        readonly=True,
        compute_sudo=True,
    )
    quality_check_ids = fields.Many2many(
        "amunet.quality.check",
        compute="_compute_dossier",
        string="Controles de calidad",
        compute_sudo=True,
    )
    material_request_ids = fields.Many2many(
        "amunet.material.request",
        compute="_compute_dossier",
        string="Solicitudes de material",
        compute_sudo=True,
    )
    equipment_ids = fields.Many2many(
        "amunet.equipment",
        compute="_compute_dossier",
        string="Equipos usados",
        compute_sudo=True,
    )
    training_ids = fields.Many2many(
        "amunet.registro.capacitacion",
        compute="_compute_dossier",
        string="Capacitaciones",
        compute_sudo=True,
    )

    quality_check_count = fields.Integer(compute="_compute_dossier", compute_sudo=True)
    material_request_count = fields.Integer(compute="_compute_dossier", compute_sudo=True)
    equipment_count = fields.Integer(compute="_compute_dossier", compute_sudo=True)
    training_count = fields.Integer(compute="_compute_dossier", compute_sudo=True)
    finding_count = fields.Integer(compute="_compute_dossier", compute_sudo=True)

    summary_html = fields.Html(compute="_compute_dossier", sanitize=False, compute_sudo=True)
    production_html = fields.Html(compute="_compute_dossier", sanitize=False, compute_sudo=True)
    quality_html = fields.Html(compute="_compute_dossier", sanitize=False, compute_sudo=True)
    material_html = fields.Html(compute="_compute_dossier", sanitize=False, compute_sudo=True)
    people_html = fields.Html(compute="_compute_dossier", sanitize=False, compute_sudo=True)
    training_html = fields.Html(compute="_compute_dossier", sanitize=False, compute_sudo=True)
    findings_html = fields.Html(compute="_compute_dossier", sanitize=False, compute_sudo=True)

    _lot_dossier_unique = models.Constraint(
        "unique(lot_id)",
        "Ya existe un expediente digital para este lote.",
    )

    @api.depends("lot_id", "lot_id.name", "lot_id.product_id")
    def _compute_name(self):
        for rec in self:
            if rec.lot_id:
                rec.name = "Expediente digital - %s" % rec.lot_id.name
            else:
                rec.name = _("Expediente digital")

    @api.depends("lot_id")
    def _compute_production_id(self):
        for rec in self:
            rec.production_id = rec._find_production(rec.lot_id)

    def _terms(self):
        self.ensure_one()
        terms = []
        if self.lot_id and self.lot_id.name:
            terms.append(self.lot_id.name)
        if self.production_id and self.production_id.origin:
            terms.append(self.production_id.origin)
        return list(dict.fromkeys([term for term in terms if term]))

    def _find_production(self, lot):
        if not lot:
            return self.env["mrp.production"].browse()
        Production = self.env["mrp.production"].sudo()
        production = Production.search([("lot_producing_ids", "in", lot.id)], limit=1)
        if production:
            return production
        QC = self.env["amunet.quality.check"].sudo()
        checks = QC.search([("lot_id", "=", lot.id)])
        if "amunet_production_id" in QC._fields:
            production = checks.mapped("amunet_production_id")[:1]
        return production

    def _find_quality_checks(self, lot, production, terms=None):
        QC = self.env["amunet.quality.check"].sudo()
        checks = QC.browse()
        if lot:
            checks |= QC.search([("lot_id", "=", lot.id)])
        if production and "amunet_production_id" in QC._fields:
            checks |= QC.search([("amunet_production_id", "=", production.id)])
        demo_hcg = any("DEMO-HCG" in term for term in (terms or []))
        for term in terms or []:
            domain = [
                "|", "|",
                ("name", "ilike", term),
                ("lot_id.name", "ilike", term),
                ("product_id.default_code", "ilike", term),
            ]
            if demo_hcg:
                domain = [
                    "&",
                    "|",
                    ("name", "ilike", "DEMO/QC/HCG"),
                    ("lot_id.name", "ilike", "DEMO-HCG"),
                ] + domain
            checks |= QC.search(domain)
        return checks.sorted("id")

    def _find_material_requests(self, terms):
        Request = self.env["amunet.material.request"].sudo()
        requests = Request.browse()
        for term in terms:
            requests |= Request.search([
                "|",
                ("note", "ilike", term),
                ("name", "ilike", term),
            ])
        return requests.sorted("id")

    def _terms_from_requests(self, requests):
        terms = []
        patterns = (
            r"\bSP[A-Z0-9]{3,}\b",
            r"\bANTICUERPO-COMPRADO\b",
            r"\bCONJUGADO-ANTI-HCG\b",
            r"\bDEMO-HCG-[A-Z0-9-]+\b",
        )
        for request in requests:
            text = " ".join(filter(None, [request.name, request.note or ""]))
            for pattern in patterns:
                terms.extend(re.findall(pattern, text))
        return list(dict.fromkeys(terms))

    def _find_training(self, terms, users):
        Training = self.env["amunet.registro.capacitacion"].sudo()
        records = Training.browse()
        for term in terms:
            records |= Training.search([("notes", "ilike", term)])
        if users:
            records |= Training.search([
                ("user_id", "in", users.ids),
                ("state", "in", ("vigente", "proxima", "vencida")),
            ])
        return records.sorted("id")

    def _find_equipment(self, production, checks):
        Equipment = self.env["amunet.equipment"].sudo()
        equipment = Equipment.browse()
        if production:
            workcenters = production.workorder_ids.mapped("workcenter_id")
            for wc in workcenters:
                if "amunet_equipment_ids" in wc._fields:
                    equipment |= wc.amunet_equipment_ids
        for line in checks.mapped("test_line_ids"):
            if "equipment_id" in line._fields and line.equipment_id:
                equipment |= line.equipment_id
        return equipment.sorted("serial_number")

    def _participants(self, production, checks, requests, trainings):
        Users = self.env["res.users"].sudo()
        users = Users.browse()
        if production:
            users |= production.create_uid
            users |= production.write_uid
        users |= checks.mapped("user_realized_id")
        users |= checks.mapped("user_verified_id")
        users |= checks.mapped("user_authorized_id")
        users |= requests.mapped("requester_id")
        users |= requests.mapped("user_requested_id")
        users |= requests.mapped("user_dispatched_id")
        users |= trainings.mapped("user_id")
        return users.filtered(lambda user: user and user.active).sorted("name")

    def _badge(self, label, value, kind="secondary"):
        return (
            '<span class="badge rounded-pill text-bg-%s">%s: %s</span>'
            % (kind, escape(label), escape(value))
        )

    def _empty(self, text):
        return '<p class="text-muted mb-0">%s</p>' % escape(text)

    def _html_table(self, headers, rows):
        if not rows:
            return self._empty("Sin registros vinculados.")
        head = "".join("<th>%s</th>" % escape(header) for header in headers)
        body = []
        for row in rows:
            body.append("<tr>%s</tr>" % "".join("<td>%s</td>" % cell for cell in row))
        return (
            '<div class="table-responsive"><table class="table table-sm table-hover align-middle">'
            "<thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>"
            % (head, "".join(body))
        )

    def _format_dt(self, value):
        return fields.Datetime.to_string(value) if value else ""

    def _compute_findings(self, production, checks, requests, equipment, trainings):
        findings = []
        if not production:
            findings.append(("warning", "No hay orden de fabricacion vinculada al lote."))
        elif production.state != "done":
            findings.append(("warning", "La orden de fabricacion no esta cerrada."))
        pending_checks = checks.filtered(lambda qc: qc.state != "done" or qc.global_result != "pass")
        for qc in pending_checks:
            findings.append(("danger", "QC pendiente o no aprobado: %s." % qc.display_name))
        open_requests = requests.filtered(lambda req: req.state not in ("closed", "done", "cancelled"))
        for req in open_requests:
            findings.append(("warning", "Solicitud de material no cerrada: %s." % req.display_name))
        for eq in equipment:
            serial = eq.serial_number or eq.display_name
            if serial in DEMO_FVA_MISSING:
                findings.append(("warning", "Equipo no reconciliado desde FVA-002: %s." % serial))
            if eq.state != "active":
                findings.append(("danger", "Equipo fuera de estado activo: %s." % serial))
            if eq.next_calibration_date and eq.next_calibration_date < fields.Date.today():
                findings.append(("danger", "Equipo con calibracion vencida: %s." % serial))
        signers = checks.mapped("user_realized_id") | checks.mapped("user_verified_id") | checks.mapped("user_authorized_id")
        signers = signers.filtered(lambda user: user and user.active)
        pin_users = self.env["amunet.quality.signature.pin"].sudo().search([
            ("user_id", "in", signers.ids)
        ]).mapped("user_id")
        missing_pin = signers - pin_users
        if missing_pin:
            findings.append((
                "warning",
                "Firmantes sin PIN/firma electronica nominal: %s." % ", ".join(missing_pin.mapped("login")),
            ))
        expired_training = trainings.filtered(lambda tr: tr.state == "vencida")
        for training in expired_training:
            findings.append(("danger", "Capacitacion vencida: %s." % training.display_name))
        if not findings:
            findings.append(("success", "Sin hallazgos bloqueantes registrados en el expediente."))
        return findings

    @api.depends(
        "lot_id",
        "production_id",
        "lot_id.amunet_lot_release_state",
        "lot_id.amunet_lot_release_hash",
    )
    def _compute_dossier(self):
        for rec in self:
            lot = rec.lot_id
            production = rec.production_id
            terms = [lot.name] if lot and lot.name else []
            if production and production.origin:
                terms.append(production.origin)
            terms = list(dict.fromkeys(terms))
            requests = rec._find_material_requests(terms)
            terms = list(dict.fromkeys(terms + rec._terms_from_requests(requests)))
            checks = rec._find_quality_checks(lot, production, terms)
            equipment = rec._find_equipment(production, checks)
            users = rec._participants(production, checks, requests, self.env["amunet.registro.capacitacion"].sudo().browse())
            trainings = rec._find_training(terms, users)
            users = rec._participants(production, checks, requests, trainings)
            findings = rec._compute_findings(production, checks, requests, equipment, trainings)

            rec.quality_check_ids = checks
            rec.material_request_ids = requests
            rec.equipment_ids = equipment
            rec.training_ids = trainings
            rec.quality_check_count = len(checks)
            rec.material_request_count = len(requests)
            rec.equipment_count = len(equipment)
            rec.training_count = len(trainings)
            rec.finding_count = len([f for f in findings if f[0] != "success"])

            release_kind = "success" if lot and lot.amunet_lot_release_state == "released" else "warning"
            prod_state = production.state if production else "sin MO"
            qc_pass = "%s/%s" % (len(checks.filtered(lambda qc: qc.global_result == "pass")), len(checks))
            req_closed = "%s/%s" % (len(requests.filtered(lambda req: req.state in ("closed", "done"))), len(requests))
            rec.summary_html = """
                <div class="o_form_label mb-2">Vista ejecutiva del expediente</div>
                <div class="d-flex flex-wrap gap-2 mb-3">
                    %s %s %s %s %s %s
                </div>
                <p class="text-muted">
                    Este expediente consolida el hilo digital del lote: fabricacion, materiales,
                    controles de calidad, firmas, equipos, capacitacion y hallazgos.
                </p>
            """ % (
                rec._badge("Lote", lot.name if lot else "", "primary"),
                rec._badge("Producto", lot.product_id.default_code if lot and lot.product_id else "", "secondary"),
                rec._badge("MO", prod_state, "info"),
                rec._badge("QC aprobados", qc_pass, "success" if checks and qc_pass.split("/")[0] == qc_pass.split("/")[1] else "warning"),
                rec._badge("Solicitudes cerradas", req_closed, "success" if requests and req_closed.split("/")[0] == req_closed.split("/")[1] else "warning"),
                rec._badge("Liberacion", lot.amunet_lot_release_state if lot else "", release_kind),
            )

            wo_rows = []
            if production:
                for wo in production.workorder_ids.sorted("sequence"):
                    eq_names = []
                    wc = wo.workcenter_id
                    if "amunet_equipment_ids" in wc._fields:
                        eq_names = wc.amunet_equipment_ids.mapped("serial_number")
                    wo_rows.append([
                        escape(wo.name),
                        escape(wc.display_name),
                        escape(wo.state),
                        escape(rec._format_dt(wo.date_start)),
                        escape(rec._format_dt(wo.date_finished)),
                        escape(", ".join(eq_names) or "Sin equipo vinculado"),
                    ])
            rec.production_html = rec._html_table(
                ["Operacion", "Area / Work center", "Estado", "Inicio", "Fin", "Equipos"],
                wo_rows,
            )

            qc_rows = []
            for qc in checks:
                qc_rows.append([
                    escape(qc.display_name),
                    escape(qc.product_id.default_code or qc.product_id.display_name),
                    escape(qc.state),
                    escape(qc.global_result),
                    escape(qc.user_realized_id.display_name or "Pendiente"),
                    escape(qc.user_verified_id.display_name or "Pendiente"),
                    escape(qc.user_authorized_id.display_name or "Pendiente"),
                ])
            rec.quality_html = rec._html_table(
                ["QC", "Producto", "Estado", "Dictamen", "Realizo", "Verifico", "Autorizo"],
                qc_rows,
            )

            request_rows = []
            for req in requests:
                request_rows.append([
                    escape(req.display_name),
                    escape(req.department_id.display_name or ""),
                    escape(req.warehouse_id.display_name or ""),
                    escape(req.state),
                    escape(req.picking_id.display_name or ""),
                    escape(req.user_requested_id.display_name or req.requester_id.display_name or ""),
                    escape(req.user_dispatched_id.display_name or ""),
                ])
            rec.material_html = rec._html_table(
                ["Solicitud", "Area", "Almacen", "Estado", "Transferencia", "Solicito", "Surtio"],
                request_rows,
            )

            people_rows = []
            for user in users:
                employee = self.env["hr.employee"].sudo().search([("user_id", "=", user.id)], limit=1)
                roles = []
                if user in checks.mapped("user_realized_id"):
                    roles.append("Realizo QC")
                if user in checks.mapped("user_verified_id"):
                    roles.append("Verifico QC")
                if user in checks.mapped("user_authorized_id"):
                    roles.append("Autorizo QC")
                if user in requests.mapped("requester_id") or user in requests.mapped("user_requested_id"):
                    roles.append("Solicito material")
                if user in requests.mapped("user_dispatched_id"):
                    roles.append("Surtio material")
                if user in trainings.mapped("user_id"):
                    roles.append("Capacitacion vigente/demo")
                people_rows.append([
                    escape(user.display_name),
                    escape(user.login or ""),
                    escape(employee.department_id.display_name if employee else ""),
                    escape(", ".join(roles) or "Participante relacionado"),
                ])
            rec.people_html = rec._html_table(["Persona", "Login", "Area", "Rol en expediente"], people_rows)

            training_rows = []
            for training in trainings:
                training_rows.append([
                    escape(training.display_name),
                    escape(training.user_id.display_name),
                    escape(training.department_id.display_name or ""),
                    escape(training.procedure_id.code or training.procedure_id.display_name or ""),
                    escape(training.state),
                    escape(str(training.expiry_date or "")),
                ])
            rec.training_html = rec._html_table(
                ["Registro", "Usuario", "Area", "SOP / PNO", "Estado", "Vence"],
                training_rows,
            )

            finding_rows = []
            for kind, text in findings:
                badge = '<span class="badge text-bg-%s">%s</span>' % (kind, escape(kind.upper()))
                finding_rows.append([badge, escape(text)])
            rec.findings_html = rec._html_table(["Tipo", "Hallazgo"], finding_rows)

    def _action_for_records(self, xmlid, model, records, name):
        self.ensure_one()
        action = self.env.ref(xmlid, raise_if_not_found=False)
        if action:
            result = action.sudo().read()[0]
        else:
            result = {
                "type": "ir.actions.act_window",
                "name": name,
                "res_model": model,
                "view_mode": "list,form",
            }
        result["domain"] = [("id", "in", records.ids)]
        if len(records) == 1:
            result.update({"res_id": records.id, "view_mode": "form"})
        return result

    def action_open_lot(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Lote"),
            "res_model": "stock.lot",
            "res_id": self.lot_id.id,
            "view_mode": "form",
        }

    def action_open_production(self):
        self.ensure_one()
        if not self.production_id:
            raise UserError(_("No hay orden de fabricacion vinculada."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Orden de fabricacion"),
            "res_model": "mrp.production",
            "res_id": self.production_id.id,
            "view_mode": "form",
        }

    def action_open_quality_checks(self):
        return self._action_for_records(
            "amunet_quality.action_amunet_quality_check",
            "amunet.quality.check",
            self.quality_check_ids,
            _("Controles de calidad"),
        )

    def action_open_material_requests(self):
        return self._action_for_records(
            "amunet_material_request.action_amunet_material_request",
            "amunet.material.request",
            self.material_request_ids,
            _("Solicitudes de material"),
        )

    def action_open_equipment(self):
        return self._action_for_records(
            "amunet_equipment_calibration.action_amunet_equipment",
            "amunet.equipment",
            self.equipment_ids,
            _("Equipos"),
        )

    def action_open_training(self):
        return self._action_for_records(
            "amunet_competencias.action_amunet_registro_capacitacion",
            "amunet.registro.capacitacion",
            self.training_ids,
            _("Capacitacion"),
        )
