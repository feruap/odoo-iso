# -*- coding: utf-8 -*-
import base64
import logging
from datetime import timedelta
from io import BytesIO

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    import qrcode
except ImportError:  # pragma: no cover
    qrcode = None
    _logger.warning(
        "amunet_hr_training: la libreria python 'qrcode' no esta "
        "instalada. El QR de auto-asistencia no podra generarse. "
        "Instalala con: pip install qrcode[pil]")

# Tolerancia de retraso para marcar on_time=True al escanear el QR.
# 10 minutos despues de date_start se considera "a tiempo".
QR_LATE_TOLERANCE_MINUTES = 10


class HrTrainingCourse(models.Model):
    """Capacitacion (curso/sesion) bajo SGC.

    Flujo de estado:
      Borrador (draft)
         -> [Confirmar Ponente] (speaker_confirmed=True)
         -> [Aprobar RH]         (hr_confirmed=True)
            cuando AMBOS son True: state pasa a 'confirmed' y se
            disparan las invitaciones automaticas.
      Confirmado (confirmed) -> Realizado (done)
      Cualquier estado -> Cancelado (cancelled)
    """
    _name = 'hr.training.course'
    _description = 'Capacitacion HR'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    name = fields.Char(
        string='Nombre de la capacitacion',
        required=True, tracking=True,
    )
    speaker_id = fields.Many2one(
        'hr.employee',
        string='Ponente',
        required=True, tracking=True,
        help='Empleado responsable de impartir la capacitacion. '
             'Solo el ponente puede pulsar "Confirmar Ponente".',
    )
    date_start = fields.Datetime(
        string='Fecha y hora de inicio', required=True, tracking=True,
    )
    date_end = fields.Datetime(
        string='Fecha y hora de fin', required=True, tracking=True,
    )
    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('confirmed', 'Confirmado'),
            ('done', 'Realizado'),
            ('cancelled', 'Cancelado'),
        ],
        string='Estado', default='draft', required=True, tracking=True,
        copy=False,
    )

    # Aprobaciones individuales que componen el paso a "Confirmado"
    speaker_confirmed = fields.Boolean(
        string='Ponente confirmo', default=False, readonly=True, copy=False,
        tracking=True,
    )
    speaker_confirmed_date = fields.Datetime(
        string='Fecha conf. ponente', readonly=True, copy=False)
    hr_confirmed = fields.Boolean(
        string='RH aprobo', default=False, readonly=True, copy=False,
        tracking=True,
    )
    hr_confirmed_date = fields.Datetime(
        string='Fecha aprob. RH', readonly=True, copy=False)
    hr_confirmed_by = fields.Many2one(
        'res.users', string='Aprobo por RH', readonly=True, copy=False)

    # Participantes y pase de lista
    department_ids = fields.Many2many(
        'hr.department',
        'hr_training_course_department_rel',
        'course_id', 'department_id',
        string='Áreas / Departamentos',
        help='Atajo: al elegir uno o varios departamentos, todos sus '
             'empleados activos se agregan automaticamente al campo '
             'Participantes. Quitar un departamento NO quita los '
             'empleados ya agregados (hay que retirarlos uno por uno).',
    )
    participant_ids = fields.Many2many(
        'hr.employee',
        'hr_training_course_employee_rel',
        'course_id', 'employee_id',
        string='Participantes (RH)',
        help='Empleados convocados a la capacitacion (definidos por RH). '
             'Se llenan manualmente o automaticamente al elegir un '
             'departamento.',
    )

    @api.onchange('department_ids')
    def _onchange_department_ids(self):
        """Cuando se agregan departamentos, sumar sus empleados
        activos al m2m de participantes (no quitar los existentes)."""
        if not self.department_ids:
            return
        new_emps = self.env['hr.employee']
        for dept in self.department_ids:
            new_emps |= dept.member_ids.filtered(lambda e: e.active)
        if new_emps:
            self.participant_ids |= new_emps
    attendance_ids = fields.One2many(
        'hr.training.attendance', 'course_id',
        string='Pase de lista', copy=False,
    )

    # Auto-asistencia por QR
    qr_attendance_url = fields.Char(
        string='URL de auto-asistencia',
        compute='_compute_qr_code', store=False, readonly=True,
        help='URL que codifica el QR. El participante (logueado) la abre '
             'desde su celular y queda registrada su asistencia.',
    )
    qr_code = fields.Binary(
        string='Codigo QR',
        compute='_compute_qr_code', store=False, readonly=True,
        attachment=False,
        help='QR de auto-asistencia. El ponente lo proyecta al inicio del '
             'curso; los participantes lo escanean con su celular (con '
             'sesion iniciada en Odoo) y se marca su asistencia y '
             'puntualidad automaticamente.',
    )

    # Datos SGC y notas
    sgc_notes = fields.Html(
        string='Notas internas SGC',
        help='Observaciones del Sistema de Gestion de Calidad. '
             'No se incluye en invitaciones ni en correos a participantes.',
    )

    # Helpers para condiciones de UI
    is_speaker_for_user = fields.Boolean(
        compute='_compute_is_speaker_for_user',
        help='True si el usuario actual es el ponente del curso.',
    )
    is_hr_user_for_user = fields.Boolean(
        compute='_compute_is_hr_user_for_user',
        help='True si el usuario actual pertenece al grupo HR.',
    )

    @api.depends_context('uid')
    @api.depends('speaker_id', 'speaker_id.user_id')
    def _compute_is_speaker_for_user(self):
        for rec in self:
            rec.is_speaker_for_user = bool(
                rec.speaker_id.user_id
                and rec.speaker_id.user_id.id == self.env.user.id
            )

    @api.depends_context('uid')
    def _compute_is_hr_user_for_user(self):
        is_hr = self.env.user.has_group('hr.group_hr_user') or \
            self.env.user.has_group('hr.group_hr_manager')
        for rec in self:
            rec.is_hr_user_for_user = is_hr

    # ============================
    # Validaciones
    # ============================
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError(_(
                    'La fecha de fin no puede ser anterior a la de inicio.'))

    # ============================
    # QR de auto-asistencia
    # ============================
    def _compute_qr_code(self):
        base = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', '') or ''
        base = base.rstrip('/')
        for rec in self:
            if not rec.id or not base:
                rec.qr_code = False
                rec.qr_attendance_url = False
                continue
            url = '%s/training/attend/%s' % (base, rec.id)
            rec.qr_attendance_url = url
            if not qrcode:
                rec.qr_code = False
                continue
            try:
                img = qrcode.make(url, box_size=10, border=2)
                buf = BytesIO()
                img.save(buf, format='PNG')
                rec.qr_code = base64.b64encode(buf.getvalue())
            except Exception:
                _logger.exception(
                    'No se pudo generar QR del curso %s', rec.id)
                rec.qr_code = False

    def action_show_qr_fullscreen(self):
        """Abre una vista limpia con el QR enorme para proyectar."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('QR de auto-asistencia'),
            'res_model': 'hr.training.course',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'amunet_hr_training.view_hr_training_course_qr_fullscreen'
            ).id,
            'target': 'new',
            'context': {'dialog_size': 'extra-large'},
        }

    def register_qr_attendance(self, employee):
        """Registra (o crea) la linea de asistencia del empleado al
        escanear el QR.

        Devuelve (success: bool, message: str, on_time: bool|None).
        """
        self.ensure_one()
        if not employee:
            return False, _(
                'Tu usuario de Odoo no esta vinculado a un empleado. '
                'Acude con Recursos Humanos.'), None
        if self.state == 'cancelled':
            return False, _(
                'Esta capacitacion fue cancelada y no admite '
                'registro de asistencia.'), None
        if self.state == 'done':
            return False, _(
                'Esta capacitacion ya fue marcada como Realizada. '
                'Tu asistencia debio quedar registrada durante el evento.'
            ), None
        if employee.id not in self.participant_ids.ids:
            return False, _(
                'No estas registrado en esta capacitacion. Acude con '
                'Recursos Humanos para que te agreguen.'), None
        # Asegurar que existe linea de asistencia para este empleado.
        Attend = self.env['hr.training.attendance'].sudo()
        line = Attend.search([
            ('course_id', '=', self.id),
            ('employee_id', '=', employee.id),
        ], limit=1)
        if not line:
            line = Attend.create({
                'course_id': self.id,
                'employee_id': employee.id,
            })
        # Calcular puntualidad: tolerancia de N minutos despues de date_start
        now = fields.Datetime.now()
        on_time = True
        if self.date_start:
            limit = self.date_start + timedelta(
                minutes=QR_LATE_TOLERANCE_MINUTES)
            on_time = now <= limit
        line.write({
            'attendance': 'attended',
            'on_time': on_time,
        })
        self.message_post(body=_(
            'Auto-asistencia por QR: %(emp)s (%(state)s).'
        ) % {
            'emp': employee.name,
            'state': _('a tiempo') if on_time else _('con retraso'),
        })
        return True, _('Asistencia registrada correctamente.'), on_time

    # ============================
    # Acciones de estado
    # ============================
    def action_speaker_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_(
                    'Solo se puede confirmar un curso en Borrador.'))
            # Solo el ponente asignado puede confirmar.
            # No hay fallback de HR: la firma del ponente queda como
            # evidencia de que es la persona que efectivamente impartira
            # el curso.
            is_speaker = bool(
                rec.speaker_id.user_id
                and rec.speaker_id.user_id.id == self.env.user.id
            )
            if not is_speaker:
                raise UserError(_(
                    'Solo el ponente asignado (%(p)s) puede pulsar '
                    '"Confirmar Ponente". Si el ponente no tiene cuenta '
                    'en Odoo o esta indisponible, edita primero el campo '
                    '"Ponente" antes de confirmar.'
                ) % {'p': rec.speaker_id.name})
            rec.write({
                'speaker_confirmed': True,
                'speaker_confirmed_date': fields.Datetime.now(),
            })
            rec.message_post(body=_(
                'Confirmacion del ponente registrada por %s.'
            ) % self.env.user.display_name)
            rec._maybe_pass_to_confirmed()
        return True

    def action_hr_approve(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_(
                    'Solo se puede aprobar un curso en Borrador.'))
            if not (self.env.user.has_group('hr.group_hr_user')
                    or self.env.user.has_group('hr.group_hr_manager')):
                raise UserError(_(
                    'Solo Recursos Humanos puede aprobar el curso.'))
            rec.write({
                'hr_confirmed': True,
                'hr_confirmed_date': fields.Datetime.now(),
                'hr_confirmed_by': self.env.user.id,
            })
            rec.message_post(body=_(
                'Aprobacion de RH registrada por %s.'
            ) % self.env.user.display_name)
            rec._maybe_pass_to_confirmed()
        return True

    def _maybe_pass_to_confirmed(self):
        """Si ambas aprobaciones estan, pasa a Confirmado y dispara
        invitaciones a los participantes."""
        for rec in self:
            if (rec.state == 'draft'
                    and rec.speaker_confirmed and rec.hr_confirmed):
                rec.state = 'confirmed'
                rec.message_post(body=_(
                    'Curso CONFIRMADO con doble aprobacion (ponente + RH).'))
                rec._send_invitations_to_participants()

    def action_done(self):
        for rec in self:
            if rec.state != 'confirmed':
                raise UserError(_(
                    'Solo un curso Confirmado puede pasar a Realizado.'))
            rec.state = 'done'
            rec.message_post(body=_('Curso marcado como Realizado.'))
        return True

    def action_cancel(self):
        for rec in self:
            if rec.state == 'cancelled':
                continue
            rec.state = 'cancelled'
            rec.message_post(body=_('Curso CANCELADO por %s.')
                             % self.env.user.display_name)
        return True

    def action_reset_to_draft(self):
        """Vuelve a Borrador (solo RH manager para casos excepcionales)."""
        if not self.env.user.has_group('hr.group_hr_manager'):
            raise UserError(_(
                'Solo el Administrador de RH puede regresar a Borrador.'))
        for rec in self:
            rec.write({
                'state': 'draft',
                'speaker_confirmed': False,
                'speaker_confirmed_date': False,
                'hr_confirmed': False,
                'hr_confirmed_date': False,
                'hr_confirmed_by': False,
            })
            rec.message_post(body=_(
                'Curso regresado a Borrador por %s.'
            ) % self.env.user.display_name)
        return True

    # ============================
    # Invitaciones por correo
    # ============================
    def _send_invitations_to_participants(self):
        """Manda el correo de invitacion a los participantes y al ponente."""
        self.ensure_one()
        if not self.participant_ids:
            return
        tmpl = self.env.ref(
            'amunet_hr_training.mail_template_training_invitation',
            raise_if_not_found=False,
        )
        if not tmpl:
            return
        # Genera attendance_ids vacios para los participantes que aun
        # no tengan registro (para que el pase de lista quede listo)
        self._ensure_attendance_lines()
        # Enviar a cada participante con email valido
        partners = self.participant_ids.mapped('work_contact_id') \
            | self.speaker_id.work_contact_id
        partner_ids = [p.id for p in partners if p and p.email]
        if partner_ids:
            self.message_post(
                body=_('Invitaciones enviadas a %d participante(s).')
                     % len(partner_ids),
                partner_ids=partner_ids,
                subtype_xmlid='mail.mt_comment',
            )
            tmpl.sudo().send_mail(self.id, force_send=False)

    def _ensure_attendance_lines(self):
        """Crea registros de attendance para participantes sin linea."""
        self.ensure_one()
        existing = self.attendance_ids.mapped('employee_id.id')
        for emp in self.participant_ids:
            if emp.id not in existing:
                self.env['hr.training.attendance'].sudo().create({
                    'course_id': self.id,
                    'employee_id': emp.id,
                })

    # ============================
    # Notificacion por cambio de fecha
    # ============================
    def write(self, vals):
        date_changed_fields = {'date_start', 'date_end'}
        notify_pending = {}
        if date_changed_fields & set(vals):
            for rec in self:
                if rec.state in ('confirmed', 'done'):
                    notify_pending[rec.id] = {
                        'old_start': rec.date_start,
                        'old_end': rec.date_end,
                    }
        res = super().write(vals)
        for rec in self:
            if rec.id in notify_pending and not self.env.context.get(
                    'skip_reschedule_notify'):
                rec._notify_reschedule(notify_pending[rec.id])
        return res

    def _notify_reschedule(self, prev):
        """Manda mensaje en chatter y por mail al ponente + participantes."""
        self.ensure_one()
        partners = self.participant_ids.mapped('work_contact_id') \
            | self.speaker_id.work_contact_id
        partner_ids = [p.id for p in partners if p and p.email]
        body = _(
            '<b>Cambio de fechas en la capacitacion %(name)s.</b><br/>'
            'Fecha anterior: %(o_start)s → %(o_end)s<br/>'
            'Nueva fecha:    %(n_start)s → %(n_end)s<br/>'
            'Por favor confirma tu disponibilidad.'
        ) % {
            'name': self.name,
            'o_start': prev['old_start'] or '-',
            'o_end': prev['old_end'] or '-',
            'n_start': self.date_start or '-',
            'n_end': self.date_end or '-',
        }
        self.message_post(
            body=body,
            partner_ids=partner_ids,
            subtype_xmlid='mail.mt_comment',
        )

    # ============================
    # Cron diario: alerta 7 dias antes
    # ============================
    @api.model
    def _cron_alerta_7_dias(self):
        """Recorre cursos en estado Borrador cuya fecha de inicio es
        exactamente 7 dias adelante. Crea actividad al grupo de RH y
        envia recordatorio al ponente."""
        from datetime import datetime, timedelta
        today = fields.Date.context_today(self)
        target = today + timedelta(days=7)
        # Rango del dia objetivo (00:00 a 23:59)
        start_dt = datetime.combine(target, datetime.min.time())
        end_dt = datetime.combine(target, datetime.max.time())
        cursos = self.search([
            ('state', '=', 'draft'),
            ('date_start', '>=', start_dt),
            ('date_start', '<=', end_dt),
        ])
        if not cursos:
            return
        todo_act_type = self.env.ref(
            'mail.mail_activity_data_todo', raise_if_not_found=False)
        if not todo_act_type:
            return
        hr_group = self.env.ref('hr.group_hr_user', raise_if_not_found=False)
        hr_users = hr_group.sudo().all_user_ids.filtered(
            lambda u: u.active and u.id != 1
        ) if hr_group else self.env['res.users']
        recordatorio_tmpl = self.env.ref(
            'amunet_hr_training.mail_template_training_speaker_reminder',
            raise_if_not_found=False,
        )
        for curso in cursos:
            # Actividad para cada usuario del grupo RH
            for u in hr_users:
                curso.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_(
                        'Capacitacion en 7 dias: %s'
                    ) % curso.name,
                    note=_(
                        'El curso %(name)s arranca el %(d)s y sigue en '
                        'Borrador. Coordinar confirmaciones y enviar a '
                        'tiempo las invitaciones.'
                    ) % {
                        'name': curso.name,
                        'd': curso.date_start,
                    },
                    user_id=u.id,
                )
            # Recordatorio al ponente
            if recordatorio_tmpl and curso.speaker_id.work_contact_id \
                    and curso.speaker_id.work_contact_id.email:
                recordatorio_tmpl.sudo().send_mail(
                    curso.id, force_send=False)
            curso.message_post(body=_(
                'Alerta automatica: este curso arranca en 7 dias y sigue '
                'en Borrador.'))
