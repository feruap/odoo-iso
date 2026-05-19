# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    amunet_operator_next_step = fields.Char(
        string='Siguiente paso',
        compute='_compute_amunet_operator_guidance',
    )
    amunet_operator_material_status = fields.Char(
        string='Materiales',
        compute='_compute_amunet_operator_guidance',
    )
    amunet_operator_quality_status = fields.Char(
        string='Calidad',
        compute='_compute_amunet_operator_guidance',
    )
    amunet_operator_time_status = fields.Char(
        string='Tiempo',
        compute='_compute_amunet_operator_guidance',
    )

    def _compute_amunet_operator_guidance(self):
        material_labels = {
            'assigned': 'Material disponible',
            'available': 'Material disponible',
            'confirmed': 'Material pendiente de surtir',
            'waiting': 'Esperando material u operacion previa',
            'late': 'Material con alerta',
            'unavailable': 'Material no disponible',
        }
        quality_labels = {
            'none': 'Sin QC requerido en esta orden',
            'to_request': 'Calidad pendiente de solicitud',
            'requested': 'Calidad solicitada',
            'approved': 'Calidad aprobada',
            'rejected': 'Calidad rechazada',
        }
        for wo in self:
            if wo.state == 'ready':
                next_step = 'Iniciar operacion'
            elif wo.state == 'progress':
                next_step = 'Terminar operacion o pausar'
            elif wo.state == 'blocked':
                next_step = 'Esperar operacion previa o materiales'
            elif wo.state == 'done':
                next_step = 'Operacion terminada'
            elif wo.state == 'cancel':
                next_step = 'Operacion cancelada'
            else:
                next_step = 'Revisar estado'

            availability = wo.production_availability or wo.production_id.reservation_state or ''
            wo.amunet_operator_next_step = next_step
            wo.amunet_operator_material_status = material_labels.get(
                availability,
                availability or 'Sin dato de materiales',
            )
            wo.amunet_operator_quality_status = quality_labels.get(
                wo.production_id.quality_analysis_status or 'none',
                wo.production_id.quality_analysis_status or 'Sin dato de calidad',
            )
            if wo.state == 'progress' and wo.is_user_working:
                wo.amunet_operator_time_status = 'Tu tiempo esta corriendo'
            elif wo.state == 'progress':
                wo.amunet_operator_time_status = 'Operacion en progreso'
            elif wo.duration:
                wo.amunet_operator_time_status = '%s min registrados' % round(wo.duration, 1)
            elif wo.duration_expected:
                wo.amunet_operator_time_status = '%s min estimados' % round(wo.duration_expected, 1)
            else:
                wo.amunet_operator_time_status = 'Sin tiempo registrado'

    def _check_amunet_operator_access(self):
        if not (
            self.env.user.has_group('amunet_production.group_production_operator')
            or self.env.user.has_group('amunet_production.group_production_supervisor')
            or self.env.user.has_group('mrp.group_mrp_user')
        ):
            raise AccessError(_('No tiene permisos para operar ordenes de trabajo de produccion.'))

    def action_amunet_operator_start(self):
        self._check_amunet_operator_access()
        for wo in self:
            if wo.state != 'ready':
                raise UserError(_('Solo se puede iniciar una operacion en estado Por realizar.'))
            wo.sudo().button_start()
            if wo.production_id:
                wo.production_id.sudo().message_post(
                    body=Markup(_(
                        'Operacion <b>%s</b> iniciada desde Mi trabajo de produccion por <b>%s</b>.'
                    ) % (wo.display_name, self.env.user.name)),
                    message_type='notification',
                )
        return True

    def action_amunet_operator_finish(self):
        self._check_amunet_operator_access()
        for wo in self:
            if wo.state != 'progress':
                raise UserError(_('Solo se puede terminar una operacion en progreso.'))
            wo.sudo().button_finish()
            if wo.production_id:
                wo.production_id.sudo().message_post(
                    body=Markup(_(
                        'Operacion <b>%s</b> terminada desde Mi trabajo de produccion por <b>%s</b>.'
                    ) % (wo.display_name, self.env.user.name)),
                    message_type='notification',
                )
        return True

    def action_amunet_open_production(self):
        self.ensure_one()
        view = self.env.ref(
            'amunet_production.view_mrp_production_operator_form',
            raise_if_not_found=False,
        )
        return {
            'type': 'ir.actions.act_window',
            'name': _('Orden de fabricacion'),
            'res_model': 'mrp.production',
            'res_id': self.production_id.id,
            'view_mode': 'form',
            'views': [(view.id, 'form')] if view else [(False, 'form')],
            'target': 'current',
        }

    def button_start(self):
        """Valida calibraciones / estado de equipos antes de arrancar.

        Si workcenter_id._amunet_check_equipment_calibration falla,
        levanta UserError. Si pasa pero el WC tiene
        amunet_no_equipment_required=True, registra una nota en el
        chatter de la mrp.production relacionada (mrp.workorder no es
        mail.thread; el log queda en la MO padre, donde es visible y
        auditable).
        """
        for wo in self:
            wc = wo.workcenter_id
            if not wc:
                continue
            res = wc._amunet_check_equipment_calibration() or {}
            if res.get('no_equipment_required') and wo.production_id:
                wo.production_id.message_post(body=_(
                    'WO <b>%s</b> (id=%s) iniciada sin equipos calibrados. '
                    'Workcenter <b>%s</b> esta marcado como '
                    '"No requiere equipo calibrado" '
                    '(amunet_no_equipment_required=True). '
                    'Excepcion autorizada en configuracion del WC. '
                    'Justificacion ISO 13485 debe estar documentada en '
                    'la nota del workcenter o en CAPA.'
                ) % (wo.name or wo.id, wo.id, wc.code or wc.name))
        return super().button_start()
