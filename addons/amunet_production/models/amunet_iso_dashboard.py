# -*- coding: utf-8 -*-

from markupsafe import escape

from odoo import api, fields, models, _


class AmunetIsoDashboard(models.Model):
    _name = "amunet.iso.dashboard"
    _description = "Centro ISO Paperless"
    _order = "id"

    name = fields.Char(default="Centro ISO Paperless", required=True)

    quality_pending_count = fields.Integer(compute="_compute_metrics", compute_sudo=True)
    lot_release_pending_count = fields.Integer(compute="_compute_metrics", compute_sudo=True)
    production_pending_count = fields.Integer(compute="_compute_metrics", compute_sudo=True)
    metrology_pending_count = fields.Integer(compute="_compute_metrics", compute_sudo=True)
    maintenance_pending_count = fields.Integer(compute="_compute_metrics", compute_sudo=True)
    training_gap_count = fields.Integer(compute="_compute_metrics", compute_sudo=True)
    training_renewal_count = fields.Integer(compute="_compute_metrics", compute_sudo=True)
    preflight_blocked_count = fields.Integer(compute="_compute_metrics", compute_sudo=True)
    missing_pin_count = fields.Integer(compute="_compute_metrics", compute_sudo=True)

    summary_html = fields.Html(compute="_compute_metrics", sanitize=False, compute_sudo=True)
    role_html = fields.Html(compute="_compute_metrics", sanitize=False, compute_sudo=True)
    paperless_html = fields.Html(compute="_compute_metrics", sanitize=False, compute_sudo=True)
    traceability_html = fields.Html(compute="_compute_metrics", sanitize=False, compute_sudo=True)

    def _env_model(self, model_name):
        try:
            return self.env[model_name].sudo()
        except KeyError:
            return False

    def _count(self, model_name, domain):
        model = self._env_model(model_name)
        if model is False:
            return 0
        return model.search_count(domain)

    def _records(self, model_name, domain, limit=None, order=None):
        model = self._env_model(model_name)
        if model is False:
            return self.env["res.users"].sudo().browse()
        return model.search(domain, limit=limit, order=order)

    def _get_missing_pin_users(self):
        Users = self._env_model("res.users")
        Pins = self._env_model("amunet.quality.signature.pin")
        if Users is False or Pins is False:
            return self.env["res.users"].sudo().browse()

        internal_group = self.env.ref("base.group_user", raise_if_not_found=False)
        domain = [("active", "=", True), ("share", "=", False)]
        if internal_group:
            domain.append(("group_ids", "in", internal_group.id))
        users = Users.search(domain)
        pinned_users = Pins.search([("user_id", "in", users.ids)]).mapped("user_id")
        return users - pinned_users

    def _badge(self, label, value, kind="secondary"):
        return (
            '<span class="badge rounded-pill text-bg-%s me-1 mb-1">%s: %s</span>'
            % (kind, escape(label), escape(value))
        )

    def _list(self, rows):
        if not rows:
            return '<p class="text-muted mb-0">Sin pendientes visibles.</p>'
        return "<ul class=\"mb-0\">%s</ul>" % "".join(
            "<li>%s</li>" % escape(row) for row in rows
        )

    def _html_table(self, headers, rows):
        if not rows:
            return '<p class="text-muted mb-0">Sin registros visibles.</p>'
        head = "".join("<th>%s</th>" % escape(header) for header in headers)
        body = []
        for row in rows:
            body.append("<tr>%s</tr>" % "".join("<td>%s</td>" % cell for cell in row))
        return (
            '<div class="table-responsive"><table class="table table-sm table-hover align-middle">'
            "<thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>"
            % (head, "".join(body))
        )

    def _pin_status_text(self, user):
        Pins = self._env_model("amunet.quality.signature.pin")
        if Pins is False:
            return "Sin PIN"
        pin_users = Pins.search([("user_id", "=", user.id)])
        return "PIN configurado" if pin_users else "Sin PIN"

    @api.depends_context("uid")
    def _compute_metrics(self):
        today = fields.Date.today()
        for rec in self:
            rec.quality_pending_count = rec._count(
                "amunet.quality.check",
                [("state", "!=", "done")],
            )
            rec.lot_release_pending_count = rec._count(
                "stock.lot",
                [
                    ("amunet_lot_release_state", "=", "pending"),
                    ("quality_check_ids", "!=", False),
                ],
            )
            rec.production_pending_count = rec._count(
                "mrp.production",
                [("state", "in", ("confirmed", "progress", "to_close"))],
            )
            rec.metrology_pending_count = rec._count(
                "amunet.calibration.program.line",
                [
                    ("program_status", "!=", "na"),
                    ("review_state", "not in", ("applied", "no_apply")),
                ],
            )
            rec.maintenance_pending_count = rec._count(
                "amunet.equipment.maintenance",
                [("state", "in", ("draft", "scheduled", "in_progress"))],
            )
            rec.training_gap_count = rec._count(
                "hr.employee",
                [("amunet_cursos_pendientes", ">", 0)],
            )
            rec.training_renewal_count = rec._count(
                "amunet.registro.capacitacion",
                [("state", "in", ("proxima", "vencida"))],
            )
            rec.preflight_blocked_count = rec._count(
                "amunet.pilot.preflight",
                [("state", "in", ("blocked", "warning"))],
            )
            missing_pin_users = rec._get_missing_pin_users()
            rec.missing_pin_count = len(missing_pin_users)

            blocker_count = (
                rec.quality_pending_count
                + rec.lot_release_pending_count
                + rec.metrology_pending_count
                + rec.maintenance_pending_count
                + rec.training_gap_count
                + rec.training_renewal_count
                + rec.preflight_blocked_count
                + rec.missing_pin_count
            )
            rec.summary_html = """
                <div class="o_form_label mb-2">Estado operativo paperless</div>
                <div class="d-flex flex-wrap gap-2 mb-3">
                    %s %s %s %s %s %s %s %s
                </div>
                <p class="text-muted mb-0">
                    Este tablero reune los pendientes que bloquean o debilitan la trazabilidad
                    ISO 13485: calidad, liberacion DHR, manufactura, metrologia,
                    mantenimiento, capacitacion y firma electronica.
                </p>
            """ % (
                rec._badge("Calidad", rec.quality_pending_count, "warning" if rec.quality_pending_count else "success"),
                rec._badge("Lotes por liberar", rec.lot_release_pending_count, "warning" if rec.lot_release_pending_count else "success"),
                rec._badge("MO abiertas", rec.production_pending_count, "info" if rec.production_pending_count else "success"),
                rec._badge("Metrologia", rec.metrology_pending_count, "warning" if rec.metrology_pending_count else "success"),
                rec._badge("Mantenimiento", rec.maintenance_pending_count, "warning" if rec.maintenance_pending_count else "success"),
                rec._badge("Capacitacion", rec.training_gap_count + rec.training_renewal_count, "danger" if rec.training_gap_count else "warning" if rec.training_renewal_count else "success"),
                rec._badge("Preflight", rec.preflight_blocked_count, "danger" if rec.preflight_blocked_count else "success"),
                rec._badge("Pendientes totales", blocker_count, "danger" if blocker_count else "success"),
            )

            role_rows = [
                "Recursos Humanos: revisar brechas por persona y renovaciones vencidas o proximas.",
                "Metrologia: cerrar lineas FVA, certificados y mantenimientos antes de liberar lotes.",
                "Produccion: cerrar MO, ordenes de trabajo y conciliacion de materiales.",
                "Calidad: cerrar QC, revisar firmas y liberar DHR solo cuando no haya bloqueos.",
                "Jefaturas: usar expedientes digitales para ver equipo, PNO, capacitacion y firma en un solo hilo.",
            ]
            if rec.missing_pin_count:
                role_rows.append(
                    "Administracion/Calidad: %s usuarios internos aun no tienen PIN nominal."
                    % rec.missing_pin_count
                )
            rec.role_html = rec._list(role_rows)

            lot_rows = []
            lots = rec._records(
                "stock.lot",
                [
                    ("amunet_lot_release_state", "=", "pending"),
                    ("quality_check_ids", "!=", False),
                ],
                limit=8,
                order="write_date desc",
            )
            for lot in lots:
                release_check = lot._get_lot_release_quality_check()
                blockers = lot._get_lot_release_blockers()
                lot_rows.append([
                    escape(lot.display_name),
                    escape(lot.product_id.display_name or ""),
                    escape(release_check.display_name if release_check else "Sin QC liberable"),
                    escape("%s bloqueo(s)" % len(blockers)),
                ])
            rec.paperless_html = rec._html_table(
                ["Lote", "Producto", "QC liberable", "Estado DHR"],
                lot_rows,
            )

            eq_rows = []
            equipment = rec._records(
                "amunet.equipment",
                [
                    "|",
                    "|",
                    ("state", "!=", "active"),
                    ("procedure_ids", "=", False),
                    "&",
                    ("calibration_required", "=", True),
                    "|",
                    ("next_calibration_date", "=", False),
                    ("next_calibration_date", "<", today),
                ],
                limit=12,
                order="department, serial_number",
            )
            for eq in equipment:
                procedures = ""
                if "procedure_ids" in eq._fields:
                    procedures = ", ".join(eq.procedure_ids.mapped("code")) or ", ".join(eq.procedure_ids.mapped("name"))
                eq_rows.append([
                    escape(eq.serial_number or eq.display_name),
                    escape(eq.department or ""),
                    escape(eq.state or ""),
                    escape(str(eq.next_calibration_date or "")),
                    escape(procedures or "Sin PNO ligado"),
                ])
            rec.traceability_html = rec._html_table(
                ["Equipo", "Area", "Estado", "Calibracion", "PNO"],
                eq_rows,
            )

    def action_refresh(self):
        return {"type": "ir.actions.client", "tag": "reload"}

    def _open_action(self, xmlid, model_name, domain, name, view_mode="list,form"):
        action = self.env.ref(xmlid, raise_if_not_found=False)
        if action:
            result = action.sudo().read()[0]
        else:
            result = {
                "type": "ir.actions.act_window",
                "name": name,
                "res_model": model_name,
                "view_mode": view_mode,
            }
        result["domain"] = domain
        return result

    def action_open_quality_work(self):
        return self._open_action(
            "amunet_quality.action_amunet_quality_my_work",
            "amunet.quality.check",
            [("state", "!=", "done")],
            _("Pendientes de calidad"),
        )

    def action_open_lot_release_pending(self):
        return self._open_action(
            "amunet_quality.action_stock_lot_quality",
            "stock.lot",
            [
                ("amunet_lot_release_state", "=", "pending"),
                ("quality_check_ids", "!=", False),
            ],
            _("Lotes pendientes de liberar"),
        )

    def action_open_lot_dossiers(self):
        return self._open_action(
            "amunet_production.action_amunet_lot_dossier",
            "amunet.lot.dossier",
            [],
            _("Expedientes digitales de lote"),
        )

    def action_open_productions(self):
        return self._open_action(
            "mrp.mrp_production_action",
            "mrp.production",
            [("state", "in", ("confirmed", "progress", "to_close"))],
            _("Ordenes de fabricacion abiertas"),
        )

    def action_open_metrology_work(self):
        return self._open_action(
            "amunet_equipment_calibration.action_amunet_metrology_my_work",
            "amunet.calibration.program.line",
            [
                ("program_status", "!=", "na"),
                ("review_state", "not in", ("applied", "no_apply")),
            ],
            _("Pendientes de metrologia"),
        )

    def action_open_maintenance_work(self):
        return self._open_action(
            "amunet_equipment_calibration.action_amunet_maintenance_my_work",
            "amunet.equipment.maintenance",
            [("state", "in", ("draft", "scheduled", "in_progress"))],
            _("Pendientes de mantenimiento"),
        )

    def action_open_training_gaps(self):
        return self._open_action(
            "amunet_competencias.action_amunet_rrhh_training_gaps",
            "hr.employee",
            [("amunet_cursos_pendientes", ">", 0)],
            _("Brechas de capacitacion"),
        )

    def action_open_training_renewals(self):
        return self._open_action(
            "amunet_competencias.action_amunet_rrhh_renewals_work",
            "amunet.registro.capacitacion",
            [("state", "in", ("proxima", "vencida"))],
            _("Renovaciones de capacitacion"),
        )

    def action_open_preflights(self):
        return self._open_action(
            "amunet_pilot_preflight.action_amunet_pilot_preflight",
            "amunet.pilot.preflight",
            [("state", "in", ("blocked", "warning"))],
            _("Preflight con bloqueos"),
        )

    def action_open_missing_pins(self):
        users = self._get_missing_pin_users()
        return self._open_action(
            "base.action_res_users",
            "res.users",
            [("id", "in", users.ids)],
            _("Usuarios sin PIN de firma"),
        )
