# -*- coding: utf-8 -*-

import hashlib
import json
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

USER_GROUP = 'amunet_estabilidad.group_stability_user'
APPROVER_GROUP = 'amunet_estabilidad.group_stability_approver'
INTERNAL_CTX = '_stability_internal'

# Campos que definen el protocolo; se congelan una vez aprobado el protocolo.
PROTOCOL_FIELDS = {
    'code', 'product_id', 'version', 'timepoints', 'duracion_meses',
    'protocolo_id', 'objetivo_meses', 'fecha_inicio', 'tolerancia_dias',
}
SIGN_FIELDS = {
    'state', 'protocol_approved_by', 'protocol_approved_on', 'protocol_hash',
    'revisa_id', 'fecha_revisa', 'aprueba_id', 'fecha_aprueba', 'final_hash',
}


class AmunetStabilityStudy(models.Model):
    _name = 'amunet.stability.study'
    _description = 'Estudio de Estabilidad (ICH Q1A)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code, version desc'

    name = fields.Char(string='Título', required=True, tracking=True)
    code = fields.Char(string='Código', required=True, index=True, tracking=True)
    version = fields.Integer(string='Versión', default=1, required=True, tracking=True)

    product_id = fields.Many2one('product.product', string='Producto', tracking=True)
    objetivo_meses = fields.Integer(string='Vida útil objetivo (meses)')
    protocolo_id = fields.Many2one('amunet.documento', string='Protocolo (PNO/Documento)')
    responsable_id = fields.Many2one('res.users', string='Responsable')
    fecha_inicio = fields.Date(string='Fecha de inicio')

    timepoints = fields.Char(
        string='Puntos de jalado (meses)', default='0,3,6,9,12,18,24,36',
        help='Lista separada por comas, ej. 0,3,6,9,12,18,24,36')
    duracion_meses = fields.Integer(string='Duración (meses)', default=36)
    tolerancia_dias = fields.Integer(
        string='Tolerancia (días)', default=15,
        help='Días tras la fecha programada antes de marcar un punto como omitido.')

    batch_ids = fields.One2many('amunet.stability.batch', 'study_id', string='Lotes')
    condition_ids = fields.One2many('amunet.stability.condition', 'study_id', string='Condiciones')
    parameter_ids = fields.One2many('amunet.stability.parameter', 'study_id', string='Parámetros / especificaciones')
    pull_ids = fields.One2many('amunet.stability.pull', 'study_id', string='Puntos de jalado')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('protocol_approved', 'Protocolo aprobado'),
        ('in_progress', 'En curso'),
        ('under_review', 'En revisión'),
        ('approved', 'Aprobado'),
        ('archived', 'Archivado'),
    ], string='Estado', default='draft', required=True, index=True, tracking=True)

    protocol_approved_by = fields.Many2one('res.users', string='Protocolo aprobado por', readonly=True)
    protocol_approved_on = fields.Datetime(string='Fecha aprobación protocolo', readonly=True)
    protocol_hash = fields.Char(string='Hash del protocolo', readonly=True, copy=False)

    conclusion = fields.Text(string='Conclusión / evaluación de tendencia')
    vida_util_concluida = fields.Char(string='Vida útil concluida')
    requiere_control_cambios = fields.Boolean(
        string='Requiere control de cambios',
        help='Si la conclusión cambia vida útil/caducidad/etiqueta/IFU, debe abrirse control de cambios.')

    capa_id = fields.Many2one('amunet.quality.capa', string='CAPA vinculada', readonly=True, copy=False)

    revisa_id = fields.Many2one('res.users', string='Revisado por', readonly=True)
    fecha_revisa = fields.Datetime(string='Fecha revisión', readonly=True)
    aprueba_id = fields.Many2one('res.users', string='Aprobado por (informe final)', readonly=True)
    fecha_aprueba = fields.Datetime(string='Fecha aprobación final', readonly=True)
    final_hash = fields.Char(string='Hash del informe final', readonly=True, copy=False)

    pull_total = fields.Integer(compute='_compute_counts')
    pull_done = fields.Integer(compute='_compute_counts')
    pull_pending = fields.Integer(compute='_compute_counts')
    oos_count = fields.Integer(compute='_compute_counts', string='Resultados fuera de especificación')

    _code_version_uniq = models.Constraint(
        'unique(code, version)',
        'Ya existe un estudio con ese código y versión.',
    )

    @api.depends('pull_ids.estado', 'pull_ids.result_ids.conforme')
    def _compute_counts(self):
        for s in self:
            s.pull_total = len(s.pull_ids)
            s.pull_done = len(s.pull_ids.filtered(lambda p: p.estado == 'done'))
            s.pull_pending = len(s.pull_ids.filtered(lambda p: p.estado in ('pending', 'in_progress')))
            s.oos_count = len(s.pull_ids.mapped('result_ids').filtered(lambda r: r.conforme == 'no'))

    def _timepoint_list(self):
        self.ensure_one()
        out = []
        for tok in (self.timepoints or '').split(','):
            tok = tok.strip()
            if tok.isdigit():
                out.append(int(tok))
        return sorted(set(out))

    # ----- inmutabilidad -----
    def write(self, vals):
        if not self.env.context.get(INTERNAL_CTX):
            bad_sign = SIGN_FIELDS.intersection(vals.keys())
            if bad_sign:
                raise UserError(_(
                    'Los campos de estado/firma solo se actualizan por el flujo de aprobación: %s'
                ) % ', '.join(sorted(bad_sign)))
            mail_fields = {'message_main_attachment_id', 'message_ids',
                           'message_follower_ids', 'activity_ids'}
            for s in self:
                if s.state == 'archived' or s.state == 'approved':
                    illegal = set(vals.keys()) - mail_fields
                    if illegal:
                        raise UserError(_(
                            'El estudio "%s" está %s y es inmutable. Crea una nueva versión. '
                            'Campos bloqueados: %s') % (s.name, s.state, ', '.join(sorted(illegal))))
                elif s.state in ('protocol_approved', 'in_progress', 'under_review'):
                    frozen = PROTOCOL_FIELDS.intersection(vals.keys())
                    if frozen:
                        raise UserError(_(
                            'El protocolo del estudio "%s" ya fue aprobado; no se pueden cambiar %s. '
                            'Crea una nueva versión.') % (s.name, ', '.join(sorted(frozen))))
        return super().write(vals)

    def unlink(self):
        for s in self:
            if s.state != 'draft' and not self.env.su:
                raise UserError(_(
                    'Solo se pueden eliminar estudios en borrador. "%s" está %s; '
                    'archívalo en su lugar.') % (s.name, s.state))
        return super().unlink()

    # ----- ciclo de vida -----
    def _build_protocol_snapshot(self):
        self.ensure_one()
        payload = {
            'code': self.code, 'version': self.version,
            'product': self.product_id.display_name,
            'timepoints': self._timepoint_list(),
            'batches': sorted(self.batch_ids.mapped('lote')),
            'conditions': sorted('%s:%s' % (c.tipo, c.name) for c in self.condition_ids),
            'parameters': sorted('%s[%s-%s/%s]' % (
                p.parametro, p.spec_min, p.spec_max, p.spec_text or '') for p in self.parameter_ids),
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def _do_approve_protocol(self):
        self.ensure_one()
        if not (self.env.su or self.env.user.has_group(APPROVER_GROUP)):
            raise AccessError(_('Solo Calidad puede aprobar el protocolo.'))
        if self.state != 'draft':
            raise UserError(_('Solo se aprueba el protocolo de estudios en borrador.'))
        if not self.batch_ids:
            raise UserError(_('Define al menos un lote.'))
        if not self.condition_ids:
            raise UserError(_('Define al menos una condición de almacenamiento.'))
        if not self.parameter_ids:
            raise UserError(_('Define los parámetros/especificaciones a evaluar.'))
        if not self._timepoint_list():
            raise UserError(_('Define los puntos de jalado.'))
        self._generate_pulls()
        self.with_context(**{INTERNAL_CTX: True}).write({
            'state': 'protocol_approved',
            'protocol_approved_by': self.env.user.id,
            'protocol_approved_on': fields.Datetime.now(),
            'protocol_hash': self._build_protocol_snapshot(),
        })
        self._log('protocol_approved', 'Protocolo aprobado por %s' % self.env.user.login)

    def _generate_pulls(self):
        self.ensure_one()
        Pull = self.env['amunet.stability.pull']
        base = self.fecha_inicio or fields.Date.context_today(self)
        for batch in self.batch_ids:
            for cond in self.condition_ids:
                for mes in self._timepoint_list():
                    exists = Pull.search_count([
                        ('study_id', '=', self.id), ('batch_id', '=', batch.id),
                        ('condition_id', '=', cond.id), ('mes', '=', mes)])
                    if exists:
                        continue
                    Pull.with_context(**{INTERNAL_CTX: True}).create({
                        'study_id': self.id, 'batch_id': batch.id,
                        'condition_id': cond.id, 'mes': mes,
                        'fecha_programada': base + relativedelta(months=mes),
                        'estado': 'pending',
                    })

    def action_open_approve_protocol(self):
        self.ensure_one()
        return self._open_sign('protocolo')

    def action_submit_review(self):
        for s in self:
            if s.state not in ('protocol_approved', 'in_progress'):
                raise UserError(_('El estudio debe estar en curso para enviarse a revisión.'))
            pend = s.pull_ids.filtered(lambda p: p.estado in ('pending', 'in_progress'))
            if pend:
                raise UserError(_('Hay %s puntos de jalado sin completar.') % len(pend))
            s.with_context(**{INTERNAL_CTX: True}).write({'state': 'under_review'})
            s._log('under_review', 'Enviado a revisión por %s' % self.env.user.login)

    def action_open_sign_final(self):
        self.ensure_one()
        return self._open_sign('aprueba')

    def _open_sign(self, role):
        return {
            'type': 'ir.actions.act_window', 'name': _('Firmar estudio'),
            'res_model': 'amunet.stability.sign.wizard', 'view_mode': 'form',
            'target': 'new', 'context': {'default_study_id': self.id, 'default_role': role},
        }

    def _do_sign_final(self, role):
        self.ensure_one()
        is_approver = self.env.su or self.env.user.has_group(APPROVER_GROUP)
        if role == 'revisa':
            if self.state != 'under_review':
                raise UserError(_('El estudio debe estar en revisión.'))
            self.with_context(**{INTERNAL_CTX: True}).write({
                'revisa_id': self.env.user.id, 'fecha_revisa': fields.Datetime.now()})
            self._log('revisa', 'Revisado por %s' % self.env.user.login)
            return True
        if not is_approver:
            raise AccessError(_('Solo Calidad puede aprobar el informe final.'))
        if self.state != 'under_review':
            raise UserError(_('El estudio debe estar en revisión antes de aprobar.'))
        if not self.revisa_id:
            raise UserError(_('El informe debe ser revisado antes de aprobarse (segregación de funciones).'))
        if self.revisa_id == self.env.user and not self.env.su:
            raise UserError(_('Quien revisa no puede ser quien aprueba.'))
        if not self.conclusion:
            raise UserError(_('Documenta la conclusión/evaluación antes de aprobar.'))
        now = fields.Datetime.now()
        snap = self._build_final_snapshot(now)
        self.with_context(**{INTERNAL_CTX: True}).write({
            'state': 'approved', 'aprueba_id': self.env.user.id,
            'fecha_aprueba': now, 'final_hash': snap})
        self._log('aprueba', 'Informe final aprobado por %s. Hash=%s' % (self.env.user.login, snap[:12]))
        return True

    def _build_final_snapshot(self, when):
        self.ensure_one()
        payload = {
            'protocol_hash': self.protocol_hash,
            'conclusion': self.conclusion,
            'vida_util': self.vida_util_concluida,
            'results': [
                (p.batch_id.lote, p.condition_id.name, p.mes, r.parameter_id.parametro,
                 r.valor_num, r.valor_text, r.conforme)
                for p in self.pull_ids.sorted(lambda x: (x.batch_id.id, x.condition_id.id, x.mes))
                for r in p.result_ids
            ],
            'aprueba': self.env.user.login, 'fecha': str(when),
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def action_new_revision(self):
        self.ensure_one()
        if not (self.env.su or self.env.user.has_group(APPROVER_GROUP)):
            raise AccessError(_('Solo un aprobador puede crear nueva versión.'))
        new = self.copy({
            'version': self.version + 1, 'state': 'draft',
            'protocol_approved_by': False, 'protocol_approved_on': False, 'protocol_hash': False,
            'revisa_id': False, 'fecha_revisa': False, 'aprueba_id': False,
            'fecha_aprueba': False, 'final_hash': False})
        return {'type': 'ir.actions.act_window', 'res_model': self._name,
                'res_id': new.id, 'view_mode': 'form', 'target': 'current'}

    def action_archive_study(self):
        if not (self.env.su or self.env.user.has_group(APPROVER_GROUP)):
            raise AccessError(_('Solo un aprobador puede archivar.'))
        self.with_context(**{INTERNAL_CTX: True}).write({'state': 'archived'})

    def action_escalate_capa(self):
        """Crea/abre una CAPA a partir de los resultados fuera de especificacion (OOS)."""
        self.ensure_one()
        if not (self.env.su or self.env.user.has_group(APPROVER_GROUP)):
            raise AccessError(_('Solo Calidad puede escalar a CAPA.'))
        capa_model = self.env['amunet.quality.capa'].sudo()
        if self.capa_id:
            capa = self.capa_id
        else:
            if not self.product_id:
                raise UserError(_('Define el producto del estudio antes de escalar a CAPA.'))
            oos = self.pull_ids.mapped('result_ids').filtered(lambda r: r.conforme == 'no')
            if not oos:
                raise UserError(_('No hay resultados fuera de especificación para escalar.'))
            detalle = '<p>Origen: estudio de estabilidad <b>%s</b> (%s).</p><ul>' % (
                self.code, self.product_id.display_name)
            for r in oos:
                detalle += '<li>Lote %s / %s / %s meses — %s: valor %s (fuera de especificación)</li>' % (
                    r.pull_id.batch_id.lote, r.pull_id.condition_id.name, r.pull_id.mes,
                    r.parameter_id.parametro, r.valor_num or r.valor_text or '')
            detalle += '</ul>'
            capa = capa_model.create({
                'title': 'OOS estabilidad %s' % self.code,
                'product_id': self.product_id.id,
                'severity': 'medium',
                'investigation_notes': detalle,
            })
            self.with_context(**{INTERNAL_CTX: True}).write({'capa_id': capa.id})
            self._log('capa', 'CAPA %s creada desde OOS por %s' % (capa.name, self.env.user.login))
        return {
            'type': 'ir.actions.act_window', 'res_model': 'amunet.quality.capa',
            'res_id': capa.id, 'view_mode': 'form', 'target': 'current',
        }

    def _log(self, event, detail):
        self.ensure_one()
        self.env['amunet.stability.audit.log'].sudo().create({
            'study_id': self.id, 'event': event,
            'user_id': self.env.user.id, 'detail': detail})

    @api.model
    def _cron_mark_missed_pulls(self):
        now = fields.Datetime.now()
        pulls = self.env['amunet.stability.pull'].search([('estado', 'in', ('pending', 'in_progress'))])
        for p in pulls:
            tol = p.study_id.tolerancia_dias or 15
            if not p.fecha_programada:
                continue
            deadline = datetime.combine(p.fecha_programada, datetime.min.time()) + timedelta(days=tol)
            if now > deadline:
                p.with_context(**{INTERNAL_CTX: True}).write({'estado': 'missed'})
                p.study_id._log('pull_missed', 'Punto %s meses (%s/%s) omitido.' % (
                    p.mes, p.batch_id.lote, p.condition_id.name))


class AmunetStabilityBatch(models.Model):
    _name = 'amunet.stability.batch'
    _description = 'Lote del estudio de estabilidad'
    _order = 'study_id, lote'

    study_id = fields.Many2one('amunet.stability.study', required=True, ondelete='cascade', index=True)
    lote = fields.Char(string='Lote / Serie', required=True)
    escala = fields.Selection([
        ('piloto', 'Piloto'), ('produccion', 'Producción'), ('laboratorio', 'Laboratorio')],
        string='Escala', default='produccion')
    fecha_fabricacion = fields.Date(string='Fecha de fabricación')
    empaque = fields.Char(string='Empaque / presentación')
    cantidad = fields.Char(string='Cantidad de muestra')
    notas = fields.Text(string='Notas')

    def _check_editable(self):
        if self.env.context.get(INTERNAL_CTX):
            return
        for r in self:
            if r.study_id.state not in ('draft',):
                raise UserError(_('El protocolo ya fue aprobado; los lotes son inmutables. Crea una nueva versión.'))

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        recs._check_editable()
        return recs

    def write(self, vals):
        self._check_editable()
        return super().write(vals)

    def unlink(self):
        self._check_editable()
        return super().unlink()


class AmunetStabilityCondition(models.Model):
    _name = 'amunet.stability.condition'
    _description = 'Condición de almacenamiento del estudio'
    _order = 'study_id, tipo'

    study_id = fields.Many2one('amunet.stability.study', required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Nombre', required=True)
    tipo = fields.Selection([
        ('largo_plazo', 'Largo plazo'),
        ('acelerado', 'Acelerado'),
        ('intermedio', 'Intermedio'),
        ('en_uso', 'En uso (open-vial)'),
        ('transporte', 'Transporte'),
    ], string='Tipo', required=True, default='largo_plazo')
    temperatura = fields.Char(string='Temperatura')
    humedad = fields.Char(string='Humedad')
    luz = fields.Char(string='Luz')
    camara = fields.Char(string='Cámara / equipo')

    def _check_editable(self):
        if self.env.context.get(INTERNAL_CTX):
            return
        for r in self:
            if r.study_id.state not in ('draft',):
                raise UserError(_('El protocolo ya fue aprobado; las condiciones son inmutables. Crea una nueva versión.'))

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        recs._check_editable()
        return recs

    def write(self, vals):
        self._check_editable()
        return super().write(vals)

    def unlink(self):
        self._check_editable()
        return super().unlink()


class AmunetStabilityParameter(models.Model):
    _name = 'amunet.stability.parameter'
    _description = 'Parámetro / especificación del estudio'
    _order = 'study_id, sequence, id'

    study_id = fields.Many2one('amunet.stability.study', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    parametro = fields.Char(string='Parámetro', required=True)
    metodo = fields.Char(string='Método')
    tipo_dato = fields.Selection([
        ('numerico', 'Numérico'), ('categorico', 'Categórico')],
        string='Tipo de dato', default='numerico', required=True)
    spec_min = fields.Float(string='Especificación mín.')
    spec_max = fields.Float(string='Especificación máx.')
    spec_text = fields.Char(string='Especificación (categórica)')
    unidad = fields.Char(string='Unidad')

    def _check_editable(self):
        if self.env.context.get(INTERNAL_CTX):
            return
        for r in self:
            if r.study_id.state not in ('draft',):
                raise UserError(_('El protocolo ya fue aprobado; las especificaciones son inmutables. Crea una nueva versión.'))

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        recs._check_editable()
        return recs

    def write(self, vals):
        self._check_editable()
        return super().write(vals)

    def unlink(self):
        self._check_editable()
        return super().unlink()


class AmunetStabilityPull(models.Model):
    _name = 'amunet.stability.pull'
    _description = 'Punto de jalado de estabilidad'
    _order = 'study_id, batch_id, condition_id, mes'

    name = fields.Char(compute='_compute_name', store=True)
    study_id = fields.Many2one('amunet.stability.study', required=True, ondelete='cascade', index=True)
    batch_id = fields.Many2one('amunet.stability.batch', required=True, ondelete='restrict')
    condition_id = fields.Many2one('amunet.stability.condition', required=True, ondelete='restrict')
    mes = fields.Integer(string='Mes', required=True)
    fecha_programada = fields.Date(string='Fecha programada', readonly=True)
    estado = fields.Selection([
        ('pending', 'Pendiente'),
        ('in_progress', 'En captura'),
        ('done', 'Completado'),
        ('missed', 'Omitido'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='pending', required=True, index=True)
    tested_by = fields.Many2one('res.users', string='Analizado por')
    fecha_real = fields.Date(string='Fecha real de análisis')
    result_ids = fields.One2many('amunet.stability.result', 'pull_id', string='Resultados')

    _pull_uniq = models.Constraint(
        'unique(study_id, batch_id, condition_id, mes)',
        'Ya existe ese punto de jalado (lote/condición/mes).',
    )

    @api.depends('batch_id.lote', 'condition_id.name', 'mes')
    def _compute_name(self):
        for p in self:
            p.name = '%s / %s / %s m' % (
                p.batch_id.lote or '', p.condition_id.name or '', p.mes)

    def action_mark_done(self):
        for p in self:
            if p.estado in ('done', 'missed', 'cancelled'):
                continue
            required_params = p.study_id.parameter_ids
            captured = p.result_ids.mapped('parameter_id')
            faltan = required_params - captured
            if faltan:
                raise UserError(_(
                    'Faltan resultados de parámetros del protocolo: %s'
                ) % ', '.join(faltan.mapped('parametro')))
            p.with_context(**{INTERNAL_CTX: True}).write({
                'estado': 'done', 'tested_by': p.tested_by.id or self.env.user.id,
                'fecha_real': p.fecha_real or fields.Date.context_today(self)})
            if p.study_id.state == 'protocol_approved':
                p.study_id.with_context(**{INTERNAL_CTX: True}).write({'state': 'in_progress'})
            p.study_id._log('pull_done', 'Punto %s m (%s/%s) completado por %s' % (
                p.mes, p.batch_id.lote, p.condition_id.name, self.env.user.login))

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get(INTERNAL_CTX) and not self.env.su:
            raise UserError(_(
                'Los puntos de jalado se generan automáticamente al aprobar el protocolo; '
                'no se crean manualmente.'))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get(INTERNAL_CTX):
            for p in self:
                if p.estado in ('done', 'missed', 'cancelled'):
                    raise UserError(_('El punto de jalado está cerrado; es inmutable.'))
                if p.study_id.state in ('approved', 'archived'):
                    raise UserError(_('El estudio está aprobado; sus puntos son inmutables.'))
        return super().write(vals)

    def unlink(self):
        if not self.env.su:
            raise AccessError(_('Los puntos de jalado no se pueden eliminar (trazabilidad).'))
        return super().unlink()


class AmunetStabilityResult(models.Model):
    _name = 'amunet.stability.result'
    _description = 'Resultado de estabilidad'
    _order = 'pull_id, id'

    pull_id = fields.Many2one('amunet.stability.pull', required=True, ondelete='cascade', index=True)
    parameter_id = fields.Many2one('amunet.stability.parameter', string='Parámetro', required=True)
    valor_num = fields.Float(string='Valor (numérico)')
    valor_text = fields.Char(string='Valor (texto)')
    unidad = fields.Char(related='parameter_id.unidad', readonly=True)
    equipo = fields.Char(string='Equipo')
    conforme = fields.Selection([
        ('si', 'Conforme'), ('no', 'Fuera de especificación')],
        string='Conformidad', compute='_compute_conforme', store=True)
    observacion = fields.Char(string='Observación')

    @api.depends('valor_num', 'valor_text', 'parameter_id.tipo_dato',
                 'parameter_id.spec_min', 'parameter_id.spec_max', 'parameter_id.spec_text')
    def _compute_conforme(self):
        for r in self:
            p = r.parameter_id
            if not p:
                r.conforme = False
                continue
            if p.tipo_dato == 'numerico':
                ok = True
                if p.spec_min or p.spec_max:
                    if p.spec_min and r.valor_num < p.spec_min:
                        ok = False
                    if p.spec_max and r.valor_num > p.spec_max:
                        ok = False
                r.conforme = 'si' if ok else 'no'
            else:
                if not p.spec_text:
                    r.conforme = 'si'
                else:
                    r.conforme = 'si' if (r.valor_text or '').strip().lower() == p.spec_text.strip().lower() else 'no'

    _result_uniq = models.Constraint(
        'unique(pull_id, parameter_id)',
        'Ya existe un resultado para ese parámetro en este punto de jalado.',
    )

    @api.constrains('parameter_id', 'pull_id')
    def _check_parameter_same_study(self):
        for r in self:
            if r.parameter_id.study_id != r.pull_id.study_id:
                raise ValidationError(_('El parámetro no pertenece al mismo estudio que el punto de jalado.'))

    def _check_pull_open(self):
        if self.env.context.get(INTERNAL_CTX):
            return
        for r in self:
            if r.pull_id.estado in ('done', 'missed', 'cancelled') or \
                    r.pull_id.study_id.state in ('approved', 'archived'):
                raise UserError(_('El punto/estudio está cerrado; los resultados son inmutables.'))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._check_pull_open()
        return records

    def write(self, vals):
        self._check_pull_open()
        return super().write(vals)

    def unlink(self):
        self._check_pull_open()
        return super().unlink()
