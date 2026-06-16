# -*- coding: utf-8 -*-

import hashlib
import json
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

OPERATOR_GROUP = 'amunet_bitacoras.group_bitacora_operator'
SUPERVISOR_GROUP = 'amunet_bitacoras.group_bitacora_supervisor'
INTERNAL_CTX = '_bitacora_internal'

# Tras firma/omisión TODO es inmutable por escritura directa. Los cambios legítimos
# (cierre de desviación por supervisor) solo se aplican vía métodos controlados que
# usan el contexto interno y validan permisos. No hay allowlist de campos por RPC.


class AmunetBitacoraEntry(models.Model):
    _name = 'amunet.bitacora.entry'
    _description = 'Registro de Bitácora'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date desc, id desc'

    name = fields.Char(string='Folio', compute='_compute_name', store=True)

    template_id = fields.Many2one(
        'amunet.bitacora.template', string='Plantilla', required=True, index=True,
        ondelete='restrict', tracking=True)
    template_version = fields.Integer(string='Versión de plantilla', readonly=True)
    tipo = fields.Selection(related='template_id.tipo', store=True, readonly=True)

    # Datos copiados (snapshot) — NO related, para preservar el histórico.
    area_id = fields.Many2one('amunet.equipment.area', string='Área', readonly=True)
    area_name = fields.Char(string='Área (texto)', readonly=True)
    pno_code = fields.Char(string='Código PNO', readonly=True)
    document_id = fields.Many2one('amunet.documento', string='PNO / Documento', readonly=True)

    period_key = fields.Char(string='Periodo', required=True, index=True, readonly=True)
    shift = fields.Integer(string='Turno', default=1, readonly=True)
    scheduled_date = fields.Date(string='Fecha programada', required=True, index=True, readonly=True)

    operator_id = fields.Many2one('res.users', string='Capturado por', tracking=True)
    datetime_done = fields.Datetime(string='Fecha/hora de captura')

    # Lecturas
    temp_value = fields.Float(string='Temperatura (°C)', tracking=True)
    hum_value = fields.Float(string='Humedad (%HR)', tracking=True)
    temp_min = fields.Float(string='Temp. mín. (spec)', readonly=True)
    temp_max = fields.Float(string='Temp. máx. (spec)', readonly=True)
    hum_min = fields.Float(string='Hum. mín. (spec)', readonly=True)
    hum_max = fields.Float(string='Hum. máx. (spec)', readonly=True)
    within_spec = fields.Boolean(string='Dentro de especificación', compute='_compute_within_spec', store=True)

    instrument_id = fields.Many2one(
        'amunet.equipment', string='Instrumento de medición',
        help='Termohigrómetro u otro instrumento usado para la lectura (temperatura/humedad).')
    instrument_name = fields.Char(string='Instrumento (snapshot)', readonly=True)

    line_ids = fields.One2many('amunet.bitacora.entry.line', 'entry_id', string='Pasos')

    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('in_progress', 'En captura'),
        ('signed', 'Firmado'),
        ('missed', 'Omitido'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='pending', required=True, index=True, tracking=True)

    # Firma
    signed_by = fields.Many2one('res.users', string='Firmado por', readonly=True)
    signed_role = fields.Selection([
        ('captured', 'Capturó'),
        ('reviewed', 'Revisó'),
        ('approved', 'Aprobó'),
    ], string='Significado de firma', readonly=True)
    signed_on = fields.Datetime(string='Fecha de firma', readonly=True)
    snapshot_hash = fields.Char(string='Hash del registro', readonly=True, copy=False)

    # Desviación
    deviation = fields.Boolean(string='Desviación', readonly=True)
    deviation_note = fields.Text(string='Nota de desviación')
    deviation_state = fields.Selection([
        ('none', 'Sin desviación'),
        ('open', 'Abierta'),
        ('closed', 'Cerrada'),
    ], string='Estado de desviación', default='none', tracking=True)
    supervisor_id = fields.Many2one('res.users', string='Cerrada por (supervisor)', readonly=True)
    supervisor_signed_on = fields.Datetime(string='Fecha cierre desviación', readonly=True)

    correction_reason = fields.Char(string='Motivo de corrección')

    _entry_period_uniq = models.Constraint(
        'unique(template_id, period_key, shift)',
        'Ya existe un registro de bitácora para esta plantilla, periodo y turno.',
    )

    @api.depends('template_id', 'scheduled_date', 'shift')
    def _compute_name(self):
        for rec in self:
            rec.name = '%s / %s%s' % (
                rec.template_id.code or 'BIT',
                rec.scheduled_date or '',
                (' T%s' % rec.shift) if rec.shift and rec.shift > 1 else '',
            )

    @api.depends('tipo', 'temp_value', 'hum_value', 'temp_min', 'temp_max', 'hum_min', 'hum_max',
                 'line_ids.done', 'line_ids.required')
    def _compute_within_spec(self):
        for rec in self:
            if rec.tipo == 'temp_humedad':
                ok = True
                if rec.temp_max > rec.temp_min:
                    ok = ok and (rec.temp_min <= rec.temp_value <= rec.temp_max)
                if rec.hum_max > rec.hum_min:
                    ok = ok and (rec.hum_min <= rec.hum_value <= rec.hum_max)
                rec.within_spec = ok
            elif rec.tipo == 'limpieza':
                pending_required = rec.line_ids.filtered(lambda l: l.required and not l.done)
                rec.within_spec = not pending_required
            else:
                rec.within_spec = True

    # ----------------------------------------------------------------
    # Inmutabilidad
    # ----------------------------------------------------------------
    def write(self, vals):
        if not self.env.context.get(INTERNAL_CTX):
            mail_fields = {'message_main_attachment_id', 'message_ids',
                           'message_follower_ids', 'activity_ids'}
            is_supervisor = self.env.user.has_group(SUPERVISOR_GROUP)
            # El supervisor puede registrar la disposición de la desviación (no editable
            # por operadores). supervisor_id/fecha solo los pone el método de cierre.
            supervisor_allowed = {'deviation_note', 'deviation_state'} if is_supervisor else set()
            for rec in self:
                if rec.state in ('signed', 'missed', 'cancelled'):
                    illegal = set(vals.keys()) - mail_fields - supervisor_allowed
                    if illegal:
                        raise UserError(_(
                            'El registro "%s" está en estado "%s" y es inmutable. '
                            'No se puede modificar: %s'
                        ) % (rec.name, rec.state, ', '.join(sorted(illegal))))
        return super().write(vals)

    def unlink(self):
        if not self.env.su and not self.env.user.has_group('base.group_system'):
            raise AccessError(_('Los registros de bitácora no se pueden eliminar (requisito de trazabilidad).'))
        for rec in self:
            if rec.state in ('signed', 'missed'):
                raise UserError(_('No se puede eliminar un registro firmado u omitido.'))
        return super().unlink()

    # ----------------------------------------------------------------
    # Captura / firma
    # ----------------------------------------------------------------
    def action_start_capture(self):
        for rec in self:
            if rec.state == 'pending':
                rec.with_context(**{INTERNAL_CTX: True}).write({
                    'state': 'in_progress',
                    'operator_id': self.env.user.id,
                    'datetime_done': fields.Datetime.now(),
                })
                rec._log_audit('capture_start', 'Captura iniciada por %s' % self.env.user.login)

    def _build_snapshot(self, extra):
        """Construye el hash sobre TODA la evidencia, incluida la firma."""
        self.ensure_one()
        payload = {
            'folio': self.name,
            'template': self.template_id.code,
            'template_version': self.template_version,
            'tipo': self.tipo,
            'area': self.area_name,
            'pno': self.pno_code,
            'period': self.period_key,
            'shift': self.shift,
            'scheduled_date': str(self.scheduled_date),
            'datetime_done': str(extra.get('datetime_done') or self.datetime_done),
            'operator': (self.operator_id.login or self.env.user.login),
            'instrument': self.instrument_id.name or '',
            'temp_value': self.temp_value,
            'hum_value': self.hum_value,
            'temp_spec': [self.temp_min, self.temp_max],
            'hum_spec': [self.hum_min, self.hum_max],
            'within_spec': self.within_spec,
            'lines': [(l.name, l.done, l.observation or '') for l in self.line_ids],
            'signed_by': self.env.user.login,
            'signed_role': extra.get('signed_role'),
            'signed_on': str(extra.get('signed_on')),
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def _do_sign(self, role):
        """Firma el registro tras validar el PIN (lo llama el wizard)."""
        self.ensure_one()
        if self.state not in ('in_progress', 'pending'):
            raise UserError(_('Solo se pueden firmar registros pendientes o en captura.'))
        if role in ('reviewed', 'approved') and not (
                self.env.su or self.env.user.has_group(SUPERVISOR_GROUP)):
            raise AccessError(_('Solo un supervisor puede firmar como "Revisó" o "Aprobó".'))
        if self.tipo == 'temp_humedad':
            if not self.instrument_id:
                raise UserError(_('Selecciona el instrumento de medición antes de firmar.'))
            if not self.datetime_done:
                raise UserError(_('Captura la lectura antes de firmar.'))
        if self.tipo == 'limpieza':
            missing = self.line_ids.filtered(lambda l: l.required and not l.done)
            if missing and not self.deviation_note:
                raise UserError(_('Faltan pasos obligatorios. Complétalos o registra la desviación.'))
        deviation = not self.within_spec
        now = fields.Datetime.now()
        vals = {
            'state': 'signed',
            'operator_id': self.operator_id.id or self.env.user.id,
            'datetime_done': self.datetime_done or now,
            'instrument_name': self.instrument_id.name or False,
            'signed_by': self.env.user.id,
            'signed_role': role,
            'signed_on': now,
            'deviation': deviation,
            'deviation_state': 'open' if deviation else 'none',
        }
        vals['snapshot_hash'] = self._build_snapshot({
            'datetime_done': vals['datetime_done'],
            'signed_role': role,
            'signed_on': now,
        })
        self.with_context(**{INTERNAL_CTX: True}).write(vals)
        self._log_audit('sign', 'Firmado (%s) por %s. Hash=%s' % (role, self.env.user.login, vals['snapshot_hash'][:12]))
        if deviation:
            self.message_post(body=_('DESVIACIÓN: registro fuera de especificación. Requiere cierre de supervisor.'))
        return True

    def action_close_deviation(self):
        if not self.env.su and not self.env.user.has_group(SUPERVISOR_GROUP):
            raise AccessError(_('Solo un supervisor puede cerrar desviaciones.'))
        for rec in self:
            if rec.deviation_state != 'open':
                continue
            if not rec.deviation_note:
                raise UserError(_('Registra la disposición de la desviación antes de cerrarla.'))
            rec.with_context(**{INTERNAL_CTX: True}).write({
                'deviation_state': 'closed',
                'supervisor_id': self.env.user.id,
                'supervisor_signed_on': fields.Datetime.now(),
            })
            rec._log_audit('deviation_close', 'Desviación cerrada por %s' % self.env.user.login)

    def _log_audit(self, event, detail):
        self.ensure_one()
        self.env['amunet.bitacora.audit.log'].sudo().create({
            'entry_id': self.id,
            'event': event,
            'user_id': self.env.user.id,
            'detail': detail,
        })

    def action_open_sign_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Firmar registro'),
            'res_model': 'amunet.bitacora.sign.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_entry_id': self.id},
        }

    def action_escalate_capa(self):
        """Abre una CAPA prellenada a partir de la desviación (Calidad completa el producto)."""
        self.ensure_one()
        if not (self.env.su or self.env.user.has_group(SUPERVISOR_GROUP)):
            raise AccessError(_('Solo un supervisor puede escalar a CAPA.'))
        notas = _(
            '<p>Origen: desviación en bitácora <b>%s</b> (%s, %s).</p>'
            '<p>Lectura/checklist fuera de especificación. Nota de desviación: %s</p>'
        ) % (self.name, self.area_name or '', self.scheduled_date or '',
             self.deviation_note or '-')
        self._log_audit('capa_escalada', 'Escalada a CAPA por %s' % self.env.user.login)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Escalar desviación a CAPA'),
            'res_model': 'amunet.quality.capa',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_title': _('Desviación bitácora %s') % self.name,
                'default_investigation_notes': notas,
                'default_severity': 'medium',
            },
        }

    # ----------------------------------------------------------------
    # Generación recurrente (cron)
    # ----------------------------------------------------------------
    @api.model
    def _cron_generate_pending(self):
        """Genera registros pendientes para plantillas activas y marca omitidos los vencidos."""
        today = fields.Date.context_today(self)
        templates = self.env['amunet.bitacora.template'].search([('state', '=', 'active')])
        created = 0
        for tpl in templates:
            for period_key, sched_date, shift in tpl._due_periods(today):
                exists = self.search_count([
                    ('template_id', '=', tpl.id),
                    ('period_key', '=', period_key),
                    ('shift', '=', shift),
                ])
                if exists:
                    continue
                self._create_from_template(tpl, period_key, sched_date, shift)
                created += 1
        # Marcar omitidos
        self._mark_missed()
        return created

    def _create_from_template(self, tpl, period_key, sched_date, shift):
        lines = [(0, 0, {
            'name': item.name,
            'sequence': item.sequence,
            'required': item.required,
        }) for item in tpl.checklist_item_ids]
        return self.create({
            'template_id': tpl.id,
            'template_version': tpl.version,
            'area_id': tpl.area_id.id,
            'area_name': tpl.area_id.name or tpl.department,
            'pno_code': tpl.pno_code,
            'document_id': tpl.document_id.id,
            'period_key': period_key,
            'shift': shift,
            'scheduled_date': sched_date,
            'temp_min': tpl.temp_min,
            'temp_max': tpl.temp_max,
            'hum_min': tpl.hum_min,
            'hum_max': tpl.hum_max,
            'state': 'pending',
            'line_ids': lines,
        })

    @api.model
    def _mark_missed(self):
        now = fields.Datetime.now()
        pendings = self.search([('state', 'in', ('pending', 'in_progress'))])
        for rec in pendings:
            tol = rec.template_id.tolerance_hours or 24
            deadline = datetime.combine(rec.scheduled_date, datetime.min.time()) + timedelta(hours=tol)
            if now > deadline:
                rec.with_context(**{INTERNAL_CTX: True}).write({'state': 'missed'})
                rec._log_audit('missed', 'Marcado como omitido por vencimiento de tolerancia.')


class AmunetBitacoraEntryLine(models.Model):
    _name = 'amunet.bitacora.entry.line'
    _description = 'Paso de bitácora (registro)'
    _order = 'sequence, id'

    entry_id = fields.Many2one(
        'amunet.bitacora.entry', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Paso', required=True, readonly=True)
    required = fields.Boolean(string='Obligatorio', readonly=True)
    done = fields.Boolean(string='Realizado')
    observation = fields.Char(string='Observación')

    def write(self, vals):
        if not self.env.context.get(INTERNAL_CTX):
            for rec in self:
                if rec.entry_id.state in ('signed', 'missed', 'cancelled'):
                    raise UserError(_('El registro está cerrado; sus pasos son inmutables.'))
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.entry_id.state in ('signed', 'missed'):
                raise UserError(_('No se pueden eliminar pasos de un registro firmado u omitido.'))
        return super().unlink()
