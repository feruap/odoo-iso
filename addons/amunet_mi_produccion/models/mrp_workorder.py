# -*- coding: utf-8 -*-
from markupsafe import Markup
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    # Alias claro del lote para la UI de piso.
    amunet_mi_lote = fields.Char(
        string='Lote', related='production_id.name', store=False)

    # Supervision de ESTA actividad (un registro de control de proceso
    # tipo supervision, ligado a esta workorder).
    amunet_mi_supervision_id = fields.Many2one(
        'amunet.process.inspection',
        string='Supervision', compute='_compute_amunet_mi_supervision')
    amunet_mi_supervision_state = fields.Selection(
        selection=[
            ('sin', 'Sin supervision'),
            ('pendiente', 'Pendiente de firma'),
            ('firmada', 'Supervisada'),
        ],
        string='Supervision', compute='_compute_amunet_mi_supervision')

    @api.depends(
        'production_id.process_inspection_ids.state',
        'production_id.process_inspection_ids.workorder_id',
        'production_id.process_inspection_ids.inspection_type',
    )
    def _compute_amunet_mi_supervision(self):
        for wo in self:
            sup = wo.production_id.process_inspection_ids.filtered(
                lambda i: i.inspection_type == 'production_supervision'
                and i.workorder_id.id == wo.id)[:1]
            wo.amunet_mi_supervision_id = sup.id if sup else False
            if not sup:
                wo.amunet_mi_supervision_state = 'sin'
            elif sup.state == 'signed':
                wo.amunet_mi_supervision_state = 'firmada'
            else:
                wo.amunet_mi_supervision_state = 'pendiente'

    # ------------------------------------------------------------------
    # Acceso
    # ------------------------------------------------------------------
    def _amunet_mi_check_access(self):
        if not (
            self.env.user.has_group('amunet_production.group_production_operator')
            or self.env.user.has_group('amunet_production.group_production_supervisor')
            or self.env.user.has_group('mrp.group_mrp_user')
        ):
            raise AccessError(_(
                'No tiene permiso para operar en Mi produccion.'))

    def _amunet_mi_trace(self, verbo):
        for wo in self:
            if wo.production_id:
                wo.production_id.sudo().message_post(
                    body=Markup(_(
                        'Actividad <b>%s</b> %s por <b>%s</b> (Mi produccion).'
                    )) % (wo.display_name, verbo, self.env.user.name),
                    message_type='notification',
                )

    # ------------------------------------------------------------------
    # Inicia / Pausa / Termina  (alimentan la orden en tiempo real)
    # ------------------------------------------------------------------
    def action_amunet_mi_start(self):
        self._amunet_mi_check_access()
        for wo in self:
            if wo.state in ('done', 'cancel'):
                raise UserError(_(
                    'La actividad %s ya esta terminada o cancelada.'
                ) % wo.display_name)
            wo.sudo().button_start()
        self._amunet_mi_trace(_('iniciada / reanudada'))
        return True

    def action_amunet_mi_pause(self):
        self._amunet_mi_check_access()
        self.sudo().button_pending()
        self._amunet_mi_trace(_('pausada'))
        return True

    def action_amunet_mi_finish(self):
        self._amunet_mi_check_access()
        for wo in self:
            if wo.state != 'progress':
                raise UserError(_(
                    'Solo se puede terminar una actividad en progreso.'))
            wo.sudo().button_finish()
        self._amunet_mi_trace(_('terminada'))
        return True

    # ------------------------------------------------------------------
    # Supervision por actividad (la firma el supervisor de produccion).
    # Si la actividad aun no tiene registro de supervision, se crea al
    # vuelo -> permite supervisar CUALQUIER actividad.
    # ------------------------------------------------------------------
    def action_amunet_mi_sign_supervision(self):
        self.ensure_one()
        if not (
            self.env.user.has_group('amunet_production.group_production_supervisor')
            or self.env.user.has_group('amunet_quality.group_quality_supervisor')
        ):
            raise AccessError(_(
                'Solo el supervisor de produccion puede firmar la '
                'supervision de la actividad.'))
        # Solo se supervisa una actividad YA CULMINADA (terminada).
        if self.state != 'done':
            raise UserError(_(
                'Solo se puede supervisar una actividad culminada. '
                '"%s" todavia no esta terminada.') % self.display_name)
        sup = self.amunet_mi_supervision_id
        if not sup:
            sup = self.env['amunet.process.inspection'].sudo().create({
                'production_id': self.production_id.id,
                'workcenter_id': self.workcenter_id.id,
                'workorder_id': self.id,
                'inspection_type': 'production_supervision',
                'inspector_id': self.env.user.id,
            })
        # Abrir el wizard de firma con PIN.
        return {
            'type': 'ir.actions.act_window',
            'name': _('Firmar supervisión'),
            'res_model': 'amunet.mi.supervision.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workorder_id': self.id,
                'default_inspection_id': sup.id,
            },
        }
