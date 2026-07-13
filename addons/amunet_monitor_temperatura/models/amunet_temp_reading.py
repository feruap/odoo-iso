# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
from .amunet_temp_area import fmt_hour12


class AmunetTempReading(models.Model):
    _name = 'amunet.temp.reading'
    _description = 'Lectura de temperatura y humedad'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, scheduled_time, area_id'

    name = fields.Char(string='Folio', compute='_compute_name', store=True)
    area_id = fields.Many2one(
        'amunet.temp.area', string='Area', required=True,
        ondelete='restrict', index=True, tracking=True)
    date = fields.Date(string='Fecha', required=True, index=True,
                       default=fields.Date.context_today)
    scheduled_time = fields.Float(string='Turno (hora)', required=True)
    scheduled_label = fields.Char(string='Turno', compute='_compute_sched_label', store=True)
    early_open_minutes = fields.Integer(
        string='Habilitar antes (min)', default=0,
        help='Minutos antes del horario en que abre la ventana de captura de '
             'esta toma. 0 = usa la tolerancia del area.')

    # Valores capturados
    temp_value = fields.Float(string='Temperatura (C)', tracking=True)
    hum_value = fields.Float(string='Humedad (%HR)', tracking=True)
    hum_required = fields.Boolean(string='Humedad obligatoria')
    observation = fields.Text(string='Observacion')

    # Limites (snapshot del area al generar)
    temp_min = fields.Float(readonly=True)
    temp_max = fields.Float(readonly=True)
    hum_min = fields.Float(readonly=True)
    hum_max = fields.Float(readonly=True)
    instrument_name = fields.Char(string='Termohigrometro', readonly=True)

    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('captured', 'Capturada'),
        ('deviation', 'Fuera de rango'),
        ('missed', 'No realizado'),
    ], string='Estado', default='pending', required=True, tracking=True, index=True)

    out_of_range = fields.Boolean(string='Fuera de rango', compute='_compute_out_of_range',
                                  store=True)
    capture_available = fields.Boolean(
        string='Captura habilitada', compute='_compute_capture_available',
        help='La captura se habilita 15 min antes del horario del turno '
             '(no se puede capturar antes).')
    window_open_label = fields.Char(
        string='Se habilita', compute='_compute_capture_available')
    captured_by = fields.Many2one('res.users', string='Capturo', readonly=True, tracking=True)
    captured_at = fields.Datetime(string='Capturado el', readonly=True)
    can_adjust = fields.Boolean(
        string='Ajustable hoy', compute='_compute_can_adjust',
        help='La lectura se puede corregir el MISMO dia de su captura, '
             'siempre que el dia no este firmado y pertenezcas al area.')

    # Desviacion (fuera de rango)
    deviation_state = fields.Selection([
        ('none', 'Sin desviacion'),
        ('open', 'Abierta'),
        ('closed', 'Cerrada'),
    ], string='Desviacion', default='none', tracking=True)
    deviation_action = fields.Text(string='Accion tomada')
    deviation_closed_by = fields.Many2one('res.users', string='Cerro desviacion', readonly=True)
    deviation_closed_at = fields.Datetime(string='Desviacion cerrada el', readonly=True)

    # Cierre diario (firma supervisor)
    day_locked = fields.Boolean(string='Dia firmado', readonly=True, copy=False)
    signed_by = fields.Many2one('res.users', string='Firmo el dia', readonly=True)
    signed_at = fields.Datetime(string='Firmado el', readonly=True)

    @api.depends('area_id', 'date', 'scheduled_time')
    def _compute_name(self):
        for r in self:
            r.name = '%s %s %s' % (
                r.area_id.code or (r.area_id.name or '')[:12], r.date or '',
                fmt_hour12(r.scheduled_time))

    @api.depends('scheduled_time')
    def _compute_sched_label(self):
        for r in self:
            r.scheduled_label = fmt_hour12(r.scheduled_time)

    @api.depends('temp_value', 'hum_value', 'temp_min', 'temp_max',
                 'hum_min', 'hum_max', 'hum_required', 'state')
    def _compute_out_of_range(self):
        for r in self:
            bad = False
            if r.state in ('captured', 'deviation'):
                if r.temp_max > r.temp_min:
                    bad = bad or not (r.temp_min <= r.temp_value <= r.temp_max)
                if r.hum_required and r.hum_max > r.hum_min:
                    bad = bad or not (r.hum_min <= r.hum_value <= r.hum_max)
            r.out_of_range = bad

    @api.depends('state', 'day_locked', 'captured_at', 'date')
    def _compute_can_adjust(self):
        """True si la lectura puede corregirse hoy: ya capturada, el dia no
        firmado, capturada el mismo dia, y el usuario pertenece al area."""
        today = fields.Date.context_today(self)
        for r in self:
            ok = False
            if r.state in ('captured', 'deviation') and not r.day_locked:
                cap_day = (fields.Datetime.context_timestamp(r, r.captured_at).date()
                           if r.captured_at else r.date)
                if cap_day == today and r.area_id.amunet_user_can_capture():
                    ok = True
            r.can_adjust = ok

    @api.model
    def _search(self, domain, **kwargs):
        """Cada usuario solo ve lecturas de las areas que captura o
        supervisa. Mery/Fernando (Configuracion) y procesos internos (su)
        ven todo."""
        if not self.env.su and not self.env.user.has_group(
                'amunet_monitor_temperatura.group_temp_manager'):
            allowed = (self.env.user.amunet_temp_my_capture_area_ids()
                       | self.env.user.amunet_temp_my_supervise_area_ids())
            domain = (domain or []) + [('area_id', 'in', allowed.ids)]
        return super()._search(domain, **kwargs)

    def _amunet_now_local(self):
        now = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        return now.hour + now.minute / 60.0, now.date()

    def _amunet_early_minutes(self):
        """Minutos de apertura anticipada de la ventana. Si la toma trae un
        valor propio (heredado del turno) se usa ese; si no, cae a la
        tolerancia del area."""
        self.ensure_one()
        return self.early_open_minutes or self.area_id.tolerance_minutes or 0

    def _compute_capture_available(self):
        for r in self:
            avail = False
            label = False
            tol = r._amunet_early_minutes() / 60.0
            open_hour = (r.scheduled_time or 0) - tol
            label = fmt_hour12(open_hour)
            if r.state in ('pending', 'missed'):
                now_hour, today = r._amunet_now_local()
                if r.date and r.date < today:
                    avail = True  # dias pasados: captura tardia permitida
                elif r.date == today:
                    avail = now_hour >= open_hour
                else:
                    avail = False  # turno futuro
            r.capture_available = avail
            r.window_open_label = label

    def _amunet_check_capture_window(self):
        """Bloquea la captura ANTES de que abra la ventana del turno
        (horario menos la tolerancia). La captura tardia si se permite."""
        self.ensure_one()
        tol = self._amunet_early_minutes() / 60.0
        open_hour = (self.scheduled_time or 0) - tol
        now_hour, today = self._amunet_now_local()
        if self.date and self.date == today and now_hour < open_hour:
            raise UserError(_(
                'Todavia no puedes capturar el turno de las %(t)s.\n\n'
                'Se habilita a partir de las %(o)s.') % {
                    't': fmt_hour12(self.scheduled_time),
                    'o': fmt_hour12(open_hour)})

    # ------------------------------------------------------------------
    # Inmutabilidad: una vez firmado el dia, no se edita.
    # ------------------------------------------------------------------
    def write(self, vals):
        internal = self.env.context.get('amunet_temp_internal')
        touch_values = any(k in vals for k in ('temp_value', 'hum_value', 'observation'))
        old_values = {}
        if not internal:
            if self.filtered('day_locked'):
                raise UserError(_(
                    'Este registro ya fue revisado y firmado por el supervisor '
                    'del dia; no se puede modificar. Si hay un error, registralo '
                    'como una correccion nueva.'))
            if touch_values:
                # Ajuste de una lectura ya capturada: solo el mismo dia, dia
                # no firmado y perteneciendo al area (los 3 permisos).
                for r in self.filtered(lambda x: x.state in ('captured', 'deviation')):
                    r._amunet_check_can_adjust()
                    old_values[r.id] = (r.temp_value, r.hum_value)
        res = super().write(vals)
        for r in self:
            if r.id in old_values:
                r._amunet_finalize_adjust(*old_values[r.id])
        return res

    def _amunet_check_can_adjust(self):
        """Valida los 3 permisos para corregir una lectura ya capturada."""
        self.ensure_one()
        if self.day_locked:
            raise UserError(_(
                'El dia ya fue firmado por el supervisor; esta lectura no se '
                'puede modificar.'))
        if not self.area_id.amunet_user_can_capture():
            raise UserError(_(
                'No perteneces al area "%s", por lo que no puedes ajustar '
                'esta lectura.') % self.area_id.name)
        today = fields.Date.context_today(self)
        cap_day = (fields.Datetime.context_timestamp(self, self.captured_at).date()
                   if self.captured_at else self.date)
        if cap_day != today:
            raise UserError(_(
                'Solo puedes corregir una lectura el MISMO dia en que se '
                'capturo (se capturo el %s). Para un cambio posterior, '
                'registra una correccion nueva.') % cap_day)

    def _amunet_finalize_adjust(self, old_temp, old_hum):
        """Tras corregir el valor: re-evalua fuera de rango / desviacion y
        deja constancia en el historial (quien, de cuanto a cuanto)."""
        self.ensure_one()
        self.invalidate_recordset(['out_of_range'])
        if self.out_of_range:
            self.with_context(amunet_temp_internal=True).write({
                'state': 'deviation', 'deviation_state': 'open'})
        else:
            vals = {'state': 'captured'}
            if self.deviation_state == 'open':
                vals['deviation_state'] = 'none'
            self.with_context(amunet_temp_internal=True).write(vals)
        self.message_post(body=_(
            'Lectura AJUSTADA por %(u)s: %(ot).1f C / %(oh).1f %%HR -> '
            '%(nt).1f C / %(nh).1f %%HR.%(oor)s') % {
            'u': self.env.user.name,
            'ot': old_temp, 'oh': old_hum,
            'nt': self.temp_value,
            'nh': self.hum_value if self.hum_required else 0.0,
            'oor': _(' FUERA DE RANGO.') if self.out_of_range else ''})

    def unlink(self):
        if self.filtered('day_locked'):
            raise UserError(_('No se puede borrar un registro ya firmado.'))
        return super().unlink()

    # ------------------------------------------------------------------
    # Cron: generar turnos de hoy y marcar No realizado los vencidos.
    # ------------------------------------------------------------------
    @api.model
    def _cron_generate_and_mark(self):
        today = fields.Date.context_today(self)
        # Amunet no trabaja sabados ni domingos: esos dias NO se generan tomas
        # de temperatura (weekday() 5=sabado, 6=domingo). La marcacion de turnos
        # vencidos de dias previos sigue corriendo normalmente mas abajo.
        if today.weekday() >= 5:
            Area = self.env['amunet.temp.area'].browse()
        else:
            Area = self.env['amunet.temp.area'].search([('active', '=', True)])
        Day = self.env['amunet.temp.daysignoff']
        for area in Area:
            if not area.slot_ids:
                continue
            if not Day.search([('area_id', '=', area.id), ('date', '=', today)], limit=1):
                Day.create({'area_id': area.id, 'date': today})
            for slot in area.slot_ids:
                exists = self.search([
                    ('area_id', '=', area.id), ('date', '=', today),
                    ('scheduled_time', '=', slot.time_hour),
                ], limit=1)
                if not exists:
                    self.with_context(amunet_temp_internal=True).create({
                        'area_id': area.id,
                        'date': today,
                        'scheduled_time': slot.time_hour,
                        'early_open_minutes': slot.early_minutes,
                        'temp_min': area.temp_min, 'temp_max': area.temp_max,
                        'hum_min': area.hum_min, 'hum_max': area.hum_max,
                        'hum_required': area.hum_required,
                        'instrument_name': area.instrument_label or False,
                    })
        # Marcar No realizado: turnos de hoy vencidos + pendientes de dias previos
        now_local = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        now_hour = now_local.hour + now_local.minute / 60.0
        for r in self.search([('date', '=', today), ('state', '=', 'pending')]):
            tol = (r.area_id.tolerance_minutes or 0) / 60.0
            if now_hour > (r.scheduled_time + tol):
                r.with_context(amunet_temp_internal=True).state = 'missed'
        self.search([('date', '<', today), ('state', '=', 'pending')]).with_context(
            amunet_temp_internal=True).write({'state': 'missed'})
        return True

    # ------------------------------------------------------------------
    # Captura (desde el wizard, con PIN)
    # ------------------------------------------------------------------
    def action_open_capture(self):
        self.ensure_one()
        if not self.area_id.amunet_user_can_capture():
            raise UserError(_(
                'No perteneces al area "%s", por lo que no puedes capturar '
                'esta lectura.') % self.area_id.name)
        if self.state not in ('pending', 'missed'):
            raise UserError(_('Esta lectura ya fue capturada.'))
        self._amunet_check_capture_window()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Capturar %s') % self.area_id.name,
            'res_model': 'amunet.temp.capture.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_reading_id': self.id},
        }

    def _apply_capture(self, temp, hum, observation):
        self.ensure_one()
        vals = {
            'temp_value': temp,
            'hum_value': hum if self.hum_required else 0.0,
            'observation': observation or False,
            'captured_by': self.env.user.id,
            'captured_at': fields.Datetime.now(),
            'state': 'captured',
        }
        self.with_context(amunet_temp_internal=True).write(vals)
        # recomputo out_of_range
        self.invalidate_recordset(['out_of_range'])
        if self.out_of_range:
            self.with_context(amunet_temp_internal=True).write({
                'state': 'deviation', 'deviation_state': 'open'})
            self._notify_supervisor_deviation()
        self.message_post(body=_(
            'Lectura capturada por %(u)s: %(t).1f C / %(h).1f %%HR.%(oor)s') % {
            'u': self.env.user.name, 't': temp,
            'h': hum if self.hum_required else 0.0,
            'oor': _(' FUERA DE RANGO.') if self.out_of_range else ''})
        return True

    def _notify_supervisor_deviation(self):
        self.ensure_one()
        sup = self.area_id._amunet_supervisor_user()
        if not sup:
            return
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            user_id=sup.id,
            summary=_('Temperatura fuera de rango: %s') % self.area_id.name,
            note=_('La lectura %(n)s (%(t).1f C / %(h).1f %%HR) salio de '
                   'especificacion. Revisa y cierra la desviacion.') % {
                'n': self.name, 't': self.temp_value, 'h': self.hum_value})

    # ------------------------------------------------------------------
    # Cierre de desviacion (supervisor, con PIN)
    # ------------------------------------------------------------------
    def action_open_close_deviation(self):
        self.ensure_one()
        if self.deviation_state != 'open':
            raise UserError(_('Esta lectura no tiene una desviacion abierta.'))
        if not self.area_id.amunet_user_is_supervisor():
            raise UserError(_(
                'Solo el supervisor del area "%s" puede cerrar la '
                'desviacion.') % self.area_id.name)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cerrar desviacion'),
            'res_model': 'amunet.temp.signoff.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_reading_id': self.id, 'default_mode': 'deviation'},
        }

    def _apply_close_deviation(self, action_text):
        self.ensure_one()
        self.with_context(amunet_temp_internal=True).write({
            'deviation_state': 'closed',
            'deviation_action': action_text,
            'deviation_closed_by': self.env.user.id,
            'deviation_closed_at': fields.Datetime.now(),
        })
        self.activity_feedback(['mail.mail_activity_data_todo'])
        self.message_post(body=_(
            'Desviacion cerrada por %(u)s. Accion: %(a)s') % {
            'u': self.env.user.name, 'a': action_text})
        return True


class AmunetTempDaySignoff(models.Model):
    _name = 'amunet.temp.daysignoff'
    _description = 'Cierre diario de monitoreo por area'
    _order = 'date desc, area_id'
    _rec_name = 'display_name'

    area_id = fields.Many2one('amunet.temp.area', string='Area', required=True,
                              ondelete='cascade', index=True)
    date = fields.Date(string='Fecha', required=True, index=True)
    display_name = fields.Char(compute='_compute_display_name')
    state = fields.Selection([
        ('pending', 'Por firmar'),
        ('signed', 'Firmado'),
    ], default='pending', required=True, index=True)
    signed_by = fields.Many2one('res.users', string='Firmo', readonly=True)
    signed_at = fields.Datetime(string='Firmado el', readonly=True)
    reading_ids = fields.Many2many('amunet.temp.reading', compute='_compute_readings')
    n_pending = fields.Integer(compute='_compute_readings')
    n_deviation_open = fields.Integer(compute='_compute_readings')

    _sql_constraints = [
        ('area_date_uniq', 'unique(area_id, date)',
         'Ya existe un cierre diario para esta area y fecha.'),
    ]

    @api.model
    def _search(self, domain, **kwargs):
        if not self.env.su and not self.env.user.has_group(
                'amunet_monitor_temperatura.group_temp_manager'):
            allowed = (self.env.user.amunet_temp_my_capture_area_ids()
                       | self.env.user.amunet_temp_my_supervise_area_ids())
            domain = (domain or []) + [('area_id', 'in', allowed.ids)]
        return super()._search(domain, **kwargs)

    @api.depends('area_id', 'date')
    def _compute_display_name(self):
        for r in self:
            r.display_name = '%s - %s' % (r.area_id.name or '', r.date or '')

    @api.depends('area_id', 'date')
    def _compute_readings(self):
        Reading = self.env['amunet.temp.reading']
        for r in self:
            reads = Reading.search([('area_id', '=', r.area_id.id), ('date', '=', r.date)])
            r.reading_ids = reads
            r.n_pending = len(reads.filtered(lambda x: x.state == 'pending'))
            r.n_deviation_open = len(reads.filtered(lambda x: x.deviation_state == 'open'))

    def action_open_sign(self):
        self.ensure_one()
        if self.state == 'signed':
            raise UserError(_('Este dia ya fue firmado.'))
        if not self.area_id.amunet_user_is_supervisor():
            raise UserError(_(
                'Solo el supervisor del area "%s" puede firmar el dia.') % self.area_id.name)
        if self.n_pending:
            raise UserError(_(
                'No puedes firmar: faltan %s lectura(s) por capturar o marcar.') % self.n_pending)
        if self.n_deviation_open:
            raise UserError(_(
                'No puedes firmar: hay %s desviacion(es) sin cerrar.') % self.n_deviation_open)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Firmar dia - %s') % self.area_id.name,
            'res_model': 'amunet.temp.signoff.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_daysignoff_id': self.id, 'default_mode': 'day'},
        }

    def _apply_sign(self):
        self.ensure_one()
        now = fields.Datetime.now()
        self.write({'state': 'signed', 'signed_by': self.env.user.id, 'signed_at': now})
        self.reading_ids.with_context(amunet_temp_internal=True).write({
            'day_locked': True, 'signed_by': self.env.user.id, 'signed_at': now})
        return True
