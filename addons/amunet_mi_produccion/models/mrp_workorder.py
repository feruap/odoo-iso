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

    # ¿El usuario actual es responsable de supervisar esta actividad?
    # True si es supervisor de la estacion (o gerente de manufactura).
    # Sirve para que "Mis supervisiones" muestre solo lo de cada jefe.
    amunet_mi_i_supervise = fields.Boolean(
        string='Yo superviso',
        compute='_compute_amunet_mi_i_supervise',
        search='_search_amunet_mi_i_supervise')

    @api.depends_context('uid')
    def _compute_amunet_mi_i_supervise(self):
        is_mgr = self.env.user.has_group('mrp.group_mrp_manager')
        for wo in self:
            wo.amunet_mi_i_supervise = is_mgr or (
                self.env.user in wo.workcenter_id.amunet_supervisor_ids)

    def _search_amunet_mi_i_supervise(self, operator, value):
        positive = (operator == '=' and value) or (operator == '!=' and not value)
        # El gerente de manufactura ve todas las estaciones.
        if self.env.user.has_group('mrp.group_mrp_manager'):
            return [(1, '=', 1)] if positive else [(0, '=', 1)]
        # Estaciones donde el usuario actual es supervisor responsable.
        my_wcs = self.env['mrp.workcenter'].search(
            [('amunet_supervisor_ids', 'in', self.env.uid)])
        if positive:
            return [('workcenter_id', 'in', my_wcs.ids)]
        return [('workcenter_id', 'not in', my_wcs.ids)]

    def _amunet_mi_worked_by_current_user(self):
        """True si el usuario actual ejecuto (registro tiempo en) esta
        actividad. Se usa para impedir la auto-supervision."""
        self.ensure_one()
        return self.env.user in self.time_ids.mapped('user_id')

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
    def _amunet_mi_block_supply(self):
        """El Surtido NO se inicia/pausa/termina con los botones genericos:
        tiene su propio flujo (Almacen surte y confirma con firma;
        Produccion recibe con firma via 'Recibir surtido'). Esto evita
        brincar el flujo y dejar el surtido en falso."""
        for wo in self:
            if wo.amunet_is_supply_workorder:
                raise UserError(_(
                    'El Surtido no se inicia ni se termina aqui.\n\n'
                    'Almacen surte el material y, cuando lo deja listo, '
                    'usa el boton "Recibir surtido" para aceptarlo con tu '
                    'firma. Asi se libera el siguiente paso.'))

    def action_amunet_mi_start(self):
        self._amunet_mi_check_access()
        self._amunet_mi_block_supply()
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
        self._amunet_mi_block_supply()
        self.sudo().button_pending()
        self._amunet_mi_trace(_('pausada'))
        return True

    def action_amunet_mi_finish(self):
        self._amunet_mi_check_access()
        self._amunet_mi_block_supply()
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
        # Segregacion de funciones: no puedes supervisar lo que tu
        # mismo ejecutaste. Debe firmarla otro supervisor.
        if self._amunet_mi_worked_by_current_user():
            raise UserError(_(
                'No puedes supervisar una actividad que tu mismo ejecutaste '
                '(segregacion de funciones). Debe firmarla otro supervisor.'))
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
