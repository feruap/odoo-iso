# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import pytz
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

    @staticmethod
    def _amunet_mi_domain_positivo(operator, value):
        """True si el dominio pide los registros donde el booleano es verdadero.
        Odoo 19 normaliza ('campo','=',True) a ('campo','in',[True]), asi que
        hay que aceptar las dos formas; si no, el filtro se invierte."""
        if isinstance(value, (list, tuple, set)):
            value = any(value)
        if operator in ('=', 'in'):
            return bool(value)
        if operator in ('!=', 'not in'):
            return not value
        return bool(value)

    @api.depends_context('uid')
    def _compute_amunet_mi_i_supervise(self):
        is_mgr = self.env.user.has_group('mrp.group_mrp_manager')
        for wo in self:
            wo.amunet_mi_i_supervise = is_mgr or (
                self.env.user in wo.workcenter_id.amunet_supervisor_ids)

    def _search_amunet_mi_i_supervise(self, operator, value):
        positive = self._amunet_mi_domain_positivo(operator, value)
        # El gerente de manufactura ve todas las estaciones.
        if self.env.user.has_group('mrp.group_mrp_manager'):
            return [(1, '=', 1)] if positive else [(0, '=', 1)]
        # Estaciones donde el usuario actual es supervisor responsable.
        my_wcs = self.env['mrp.workcenter'].search(
            [('amunet_supervisor_ids', 'in', self.env.uid)])
        if positive:
            return [('workcenter_id', 'in', my_wcs.ids)]
        return [('workcenter_id', 'not in', my_wcs.ids)]

    # ------------------------------------------------------------------
    # Mi dia: ¿esta actividad es de MI puesto?
    # El puesto son las estaciones asignadas al empleado del usuario
    # (hr.employee.amunet_mi_workcenter_ids). Sin estaciones asignadas o sin
    # empleado ligado se ve todo, para no dejar a nadie sin pantalla.
    # ------------------------------------------------------------------
    amunet_mi_es_mio = fields.Boolean(
        string='De mi puesto',
        compute='_compute_amunet_mi_es_mio',
        search='_search_amunet_mi_es_mio')

    @api.model
    def _amunet_mi_workcenters_del_usuario(self):
        """Estaciones del puesto del usuario actual. Vacio = sin filtro."""
        emp = self.env['hr.employee'].sudo().search(
            [('user_id', '=', self.env.uid)], limit=1)
        return emp.amunet_mi_workcenter_ids if emp else self.env['mrp.workcenter']

    @api.depends_context('uid')
    def _compute_amunet_mi_es_mio(self):
        wcs = self._amunet_mi_workcenters_del_usuario()
        for wo in self:
            wo.amunet_mi_es_mio = (not wcs) or (wo.workcenter_id in wcs)

    def _search_amunet_mi_es_mio(self, operator, value):
        positive = self._amunet_mi_domain_positivo(operator, value)
        wcs = self._amunet_mi_workcenters_del_usuario()
        if not wcs:
            return [(1, '=', 1)] if positive else [(0, '=', 1)]
        if positive:
            return [('workcenter_id', 'in', wcs.ids)]
        return [('workcenter_id', 'not in', wcs.ids)]

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

    # ------------------------------------------------------------------
    # Solo "Terminar" (decision de Fernando, 3-sep-2026): el operador no
    # marca el inicio. El inicio se INFIERE como el ultimo de estos momentos:
    #   a) cuando esa persona termino su actividad anterior (hoy),
    #   b) cuando quedo lista esta actividad (termino el paso previo del lote),
    #   c) la hora de entrada del turno (checador de hoy; si no hay, el
    #      horario del calendario de la persona/estacion).
    # Con eso la orden recibe el tiempo real igual que antes, sin boton de
    # inicio. Un lote suelto puede quedar inflado (juntas, esperas); lo que
    # se usa para programar es la mediana de muchos lotes.
    # ------------------------------------------------------------------
    def _amunet_mi_tz(self):
        return pytz.timezone(self.env.user.tz or 'America/Mexico_City')

    def _amunet_mi_inicio_turno(self, ahora):
        """Hora de entrada de hoy (UTC naive) para el usuario actual."""
        tz = self._amunet_mi_tz()
        hoy_local = ahora.replace(tzinfo=pytz.utc).astimezone(tz).date()
        emp = self.env['hr.employee'].sudo().search(
            [('user_id', '=', self.env.uid)], limit=1)
        # a) checador de hoy
        if emp and 'hr.attendance' in self.env:
            ini_dia_utc = tz.localize(datetime.combine(hoy_local, datetime.min.time())).astimezone(pytz.utc).replace(tzinfo=None)
            att = self.env['hr.attendance'].sudo().search(
                [('employee_id', '=', emp.id), ('check_in', '>=', ini_dia_utc)],
                order='check_in asc', limit=1)
            if att:
                return att.check_in
        # b) calendario de la estacion (es el de planta, en hora de Mexico);
        #    si no tiene, el del empleado. Primer bloque del dia.
        cal = self.workcenter_id.resource_calendar_id or (emp.resource_calendar_id if emp else False)
        hora = 8.0
        if cal:
            att = cal.attendance_ids.filtered(
                lambda a: int(a.dayofweek) == hoy_local.weekday())
            if att:
                hora = min(att.mapped('hour_from'))
        cal_tz = pytz.timezone(cal.tz) if cal and cal.tz else tz
        local = cal_tz.localize(datetime.combine(hoy_local, datetime.min.time()) + timedelta(hours=hora))
        return local.astimezone(pytz.utc).replace(tzinfo=None)

    def _amunet_mi_inferir_inicio(self, ahora):
        self.ensure_one()
        candidatos = [self._amunet_mi_inicio_turno(ahora)]
        # a) fin de la actividad anterior de esta persona (hoy)
        prev = self.env['mrp.workcenter.productivity'].sudo().search(
            [('user_id', '=', self.env.uid), ('date_end', '!=', False),
             ('date_end', '>=', candidatos[0]), ('workorder_id', '!=', self.id)],
            order='date_end desc', limit=1)
        if prev:
            candidatos.append(prev.date_end)
        # b) cuando quedo lista: fin del paso previo del mismo lote
        previos = self.production_id.workorder_ids.filtered(
            lambda w: w.id != self.id and w.state == 'done' and w.date_finished
            and (w.sequence, w.id) < (self.sequence, self.id))
        if previos:
            candidatos.append(max(previos.mapped('date_finished')))
        inicio = max(c for c in candidatos if c)
        if inicio >= ahora:
            inicio = ahora - timedelta(minutes=max(self.duration_expected or 1.0, 1.0))
        return inicio

    def action_amunet_mi_finish(self):
        self._amunet_mi_check_access()
        self._amunet_mi_block_supply()
        ahora = fields.Datetime.now()
        for wo in self:
            if wo.state not in ('ready', 'progress'):
                raise UserError(_(
                    'Solo se puede terminar una actividad lista o en progreso '
                    '("%s" esta en %s).') % (wo.display_name, wo.state))
            abierto = wo.time_ids.filtered(lambda t: not t.date_end and t.user_id == self.env.user)
            if not abierto:
                inicio = wo._amunet_mi_inferir_inicio(ahora)
                wo.sudo().button_start()
                linea = wo.time_ids.filtered(lambda t: not t.date_end and t.user_id == self.env.user)[:1]
                if linea:
                    linea.sudo().write({'date_start': inicio})
                if not wo.date_start or wo.date_start > inicio:
                    wo.sudo().with_context(bypass_duration_calculation=True).write({'date_start': inicio})
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
