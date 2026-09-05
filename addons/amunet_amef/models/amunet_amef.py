# -*- coding: utf-8 -*-

import hashlib
import json

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

USER_GROUP = 'amunet_amef.group_amef_user'
APPROVER_GROUP = 'amunet_amef.group_amef_approver'
INTERNAL_CTX = '_amef_internal'

NIVEL_SELECTION = [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')]
ACEPT_SELECTION = [
    ('aceptable', 'Aceptable'),
    ('alarp', 'Tolerable (ALARP)'),
    ('inaceptable', 'Inaceptable'),
]


def _acceptability(index):
    """Matriz de aceptabilidad por defecto (S 1-5 x P 1-5 = 1-25).
    Configurable a futuro; por ahora umbrales documentados."""
    if not index:
        return False
    if index <= 3:
        return 'aceptable'
    if index <= 9:
        return 'alarp'
    return 'inaceptable'


class AmunetAmef(models.Model):
    _name = 'amunet.amef'
    _description = 'Expediente de Análisis de Riesgo (AMEF / ISO 14971)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code, version desc'

    name = fields.Char(string='Título', required=True, tracking=True)
    code = fields.Char(string='Código', required=True, index=True, tracking=True)
    version = fields.Integer(string='Versión', default=1, required=True, tracking=True)
    tipo = fields.Selection([
        ('proceso', 'De proceso'),
        ('diseno', 'De diseño'),
        ('producto', 'De producto'),
    ], string='Tipo', default='proceso', required=True, tracking=True)

    product_proceso = fields.Char(string='Producto / Proceso (texto)')
    product_id = fields.Many2one('product.product', string='Producto')
    area = fields.Char(string='Área')
    document_id = fields.Many2one('amunet.documento', string='PNO / Documento controlado')

    uso_previsto = fields.Text(string='Uso previsto')
    mal_uso_previsible = fields.Text(string='Mal uso razonablemente previsible')
    alcance = fields.Text(string='Alcance del análisis')
    equipo = fields.Text(string='Equipo participante')
    fecha = fields.Date(string='Fecha', default=fields.Date.context_today)

    metodologia = fields.Selection([
        ('iso14971', 'ISO 14971 (matriz S x P)'),
        ('ambos', 'ISO 14971 + AMEF (S/O/D)'),
    ], string='Metodología', default='ambos', required=True)

    line_ids = fields.One2many('amunet.amef.line', 'amef_id', string='Líneas de riesgo')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('in_review', 'En revisión'),
        ('approved', 'Aprobado'),
        ('archived', 'Archivado'),
    ], string='Estado', default='draft', required=True, tracking=True)

    riesgo_global_residual = fields.Selection(
        ACEPT_SELECTION, string='Riesgo global residual', tracking=True,
        help='Evaluación global del riesgo residual del producto/proceso (ISO 14971 cláusula 8).')
    beneficio_riesgo = fields.Text(
        string='Justificación beneficio/riesgo',
        help='Requerida cuando el riesgo residual global no es plenamente aceptable.')

    fecha_proxima_revision = fields.Date(string='Próxima revisión periódica')
    gatillos_revision = fields.Text(
        string='Gatillos de revisión',
        help='Eventos que disparan revisión: queja, desviación, CAPA, cambio, lote rechazado, vigilancia.')

    responsable_id = fields.Many2one('res.users', string='Responsable', tracking=True)
    revisa_id = fields.Many2one('res.users', string='Revisado por', readonly=True)
    fecha_revisa = fields.Datetime(string='Fecha de revisión', readonly=True)
    aprueba_id = fields.Many2one('res.users', string='Aprobado por', readonly=True)
    fecha_aprueba = fields.Datetime(string='Fecha de aprobación', readonly=True)
    snapshot_hash = fields.Char(string='Hash del expediente', readonly=True, copy=False)

    line_count = fields.Integer(compute='_compute_counts')
    inaceptable_count = fields.Integer(compute='_compute_counts', string='Líneas inaceptables')

    _code_version_uniq = models.Constraint(
        'unique(code, version)',
        'Ya existe un AMEF con ese código y versión.',
    )

    @api.depends('line_ids.aceptabilidad_residual')
    def _compute_counts(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)
            rec.inaceptable_count = len(rec.line_ids.filtered(
                lambda l: l.aceptabilidad_residual == 'inaceptable'))

    # Campos de firma/estado: solo se escriben por el flujo controlado (contexto interno).
    SIGN_FIELDS = {'revisa_id', 'fecha_revisa', 'aprueba_id', 'fecha_aprueba',
                   'snapshot_hash', 'state'}

    # ----- inmutabilidad -----
    def write(self, vals):
        if not self.env.context.get(INTERNAL_CTX):
            bad = self.SIGN_FIELDS.intersection(vals.keys())
            if bad:
                raise UserError(_(
                    'Los campos de firma/estado solo se actualizan por el flujo de '
                    'revisión/aprobación (botón Firmar): %s'
                ) % ', '.join(sorted(bad)))
            mail_fields = {'message_main_attachment_id', 'message_ids',
                           'message_follower_ids', 'activity_ids'}
            for rec in self:
                if rec.state in ('approved', 'archived'):
                    illegal = set(vals.keys()) - mail_fields
                    if illegal:
                        raise UserError(_(
                            'El AMEF "%s" está %s y es inmutable. Para cambiarlo crea una '
                            'nueva versión. Campos bloqueados: %s'
                        ) % (rec.name, rec.state, ', '.join(sorted(illegal))))
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state in ('approved', 'archived') and not self.env.su:
                raise UserError(_('No se puede eliminar un AMEF aprobado o archivado.'))
        return super().unlink()

    # ----- ciclo de vida -----
    def action_submit_review(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Solo se envían a revisión los AMEF en borrador.'))
            if not rec.line_ids:
                raise UserError(_('No se puede enviar a revisión un AMEF sin líneas de riesgo.'))
            rec.with_context(**{INTERNAL_CTX: True}).write({'state': 'in_review'})
            rec._log('submit_review', 'Enviado a revisión por %s' % self.env.user.login)

    def _build_snapshot(self, extra):
        self.ensure_one()
        payload = {
            'code': self.code, 'version': self.version, 'name': self.name,
            'tipo': self.tipo, 'product_proceso': self.product_proceso,
            'uso_previsto': self.uso_previsto, 'riesgo_global': self.riesgo_global_residual,
            'lines': [
                (l.sequence, l.hazard, l.situacion_peligrosa, l.harm,
                 l.severidad_inicial, l.probabilidad_inicial, l.aceptabilidad_inicial,
                 l.severidad_residual, l.probabilidad_residual, l.aceptabilidad_residual,
                 [(c.descripcion, c.tipo_control) for c in l.control_ids])
                for l in self.line_ids.sorted('sequence')
            ],
            'aprueba': self.env.user.login,
            'fecha_aprueba': str(extra.get('fecha_aprueba')),
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def _do_approve(self, role):
        """Aprueba/revisa el AMEF tras validar PIN (llamado por el wizard)."""
        self.ensure_one()
        is_approver = self.env.su or self.env.user.has_group(APPROVER_GROUP)
        if role == 'aprueba' and not is_approver:
            raise AccessError(_('Solo un aprobador de Calidad puede aprobar el AMEF.'))
        if role == 'revisa':
            if self.state != 'in_review':
                raise UserError(_('El AMEF debe estar en revisión.'))
            self.with_context(**{INTERNAL_CTX: True}).write({
                'revisa_id': self.env.user.id, 'fecha_revisa': fields.Datetime.now()})
            self._log('revisa', 'Revisado por %s' % self.env.user.login)
            return True
        # aprobar
        if self.state != 'in_review':
            raise UserError(_('El AMEF debe estar en revisión antes de aprobar.'))
        if not self.revisa_id:
            raise UserError(_('El AMEF debe ser revisado antes de aprobarse (segregación de funciones).'))
        if self.revisa_id == self.env.user and not self.env.su:
            raise UserError(_('Quien revisa no puede ser quien aprueba (segregación de funciones).'))
        self._check_complete_for_approval()
        now = fields.Datetime.now()
        snap = self._build_snapshot({'fecha_aprueba': now})
        self.with_context(**{INTERNAL_CTX: True}).write({
            'state': 'approved', 'aprueba_id': self.env.user.id,
            'fecha_aprueba': now, 'snapshot_hash': snap})
        self._log('aprueba', 'Aprobado por %s. Hash=%s' % (self.env.user.login, snap[:12]))
        return True

    def _check_complete_for_approval(self):
        """ISO 14971: no se aprueba un expediente incompleto."""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('El AMEF no tiene líneas de riesgo.'))
        if not self.riesgo_global_residual:
            raise UserError(_('Define la evaluación de riesgo global residual antes de aprobar.'))
        if self.riesgo_global_residual != 'aceptable' and not self.beneficio_riesgo:
            raise UserError(_(
                'El riesgo global residual no es aceptable: documenta la justificación '
                'beneficio/riesgo antes de aprobar.'))
        for l in self.line_ids:
            faltan = []
            if not l.hazard:
                faltan.append(_('peligro'))
            if not l.harm:
                faltan.append(_('daño'))
            if not (l.severidad_inicial and l.probabilidad_inicial):
                faltan.append(_('riesgo inicial (S/P)'))
            if not (l.severidad_residual and l.probabilidad_residual):
                faltan.append(_('riesgo residual (S/P)'))
            if l.aceptabilidad_residual == 'inaceptable' and not l.justificacion:
                faltan.append(_('justificación de riesgo residual inaceptable'))
            if faltan:
                raise UserError(_('La línea "%s" está incompleta: falta %s.') % (
                    l.name, ', '.join(faltan)))

    def action_open_sign_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'name': _('Firmar AMEF'),
            'res_model': 'amunet.amef.sign.wizard', 'view_mode': 'form',
            'target': 'new', 'context': {'default_amef_id': self.id},
        }

    def action_new_revision(self):
        self.ensure_one()
        if not (self.env.su or self.env.user.has_group(APPROVER_GROUP)):
            raise AccessError(_('Solo un aprobador puede crear nueva revisión.'))
        new = self.copy({
            'version': self.version + 1, 'state': 'draft',
            'revisa_id': False, 'fecha_revisa': False,
            'aprueba_id': False, 'fecha_aprueba': False, 'snapshot_hash': False})
        new.message_post(body=_('Nueva revisión creada desde la versión %s.') % self.version)
        return {'type': 'ir.actions.act_window', 'res_model': self._name,
                'res_id': new.id, 'view_mode': 'form', 'target': 'current'}

    def action_archive_amef(self):
        if not (self.env.su or self.env.user.has_group(APPROVER_GROUP)):
            raise AccessError(_('Solo un aprobador puede archivar.'))
        self.with_context(**{INTERNAL_CTX: True}).write({'state': 'archived'})

    def action_escalate_capa(self):
        """Abre una CAPA prellenada a partir de las líneas de riesgo inaceptable."""
        self.ensure_one()
        if not (self.env.su or self.env.user.has_group(APPROVER_GROUP)):
            raise AccessError(_('Solo Calidad puede escalar a CAPA.'))
        lineas = self.line_ids.filtered(lambda l: l.aceptabilidad_residual == 'inaceptable')
        if not lineas:
            raise UserError(_('No hay líneas con riesgo residual inaceptable.'))
        notas = _('<p>Origen: AMEF <b>%s</b> (%s).</p><ul>') % (self.code, self.product_proceso or '')
        for l in lineas:
            notas += _('<li>%s — peligro: %s; daño: %s (riesgo residual inaceptable)</li>') % (
                l.name, l.hazard or '', l.harm or '')
        notas += '</ul>'
        self._log('capa_escalada', 'Escalada a CAPA por %s' % self.env.user.login)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Escalar riesgo a CAPA'),
            'res_model': 'amunet.quality.capa',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_title': _('Riesgo inaceptable AMEF %s') % self.code,
                'default_investigation_notes': notas,
                'default_severity': 'critical',
                'default_product_id': self.product_id.id if self.product_id else False,
            },
        }

    def _log(self, event, detail):
        self.ensure_one()
        self.env['amunet.amef.audit.log'].sudo().create({
            'amef_id': self.id, 'event': event,
            'user_id': self.env.user.id, 'detail': detail})


class AmunetAmefLine(models.Model):
    _name = 'amunet.amef.line'
    _description = 'Línea de Análisis de Riesgo'
    _order = 'amef_id, sequence, id'

    amef_id = fields.Many2one('amunet.amef', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Función / Elemento', required=True)

    # ISO 14971: peligro -> situación peligrosa -> daño
    hazard = fields.Char(string='Peligro')
    situacion_peligrosa = fields.Text(string='Situación peligrosa')
    secuencia_eventos = fields.Text(string='Secuencia de eventos')
    harm = fields.Char(string='Daño')

    # Riesgo inicial (matriz S x P)
    severidad_inicial = fields.Selection(NIVEL_SELECTION, string='Severidad inicial')
    probabilidad_inicial = fields.Selection(NIVEL_SELECTION, string='Probabilidad inicial')
    indice_inicial = fields.Integer(compute='_compute_riesgo', store=True, string='Índice inicial')
    aceptabilidad_inicial = fields.Selection(
        ACEPT_SELECTION, compute='_compute_riesgo', store=True, string='Aceptabilidad inicial')

    # AMEF secundario (S/O/D)
    amef_sev = fields.Integer(string='AMEF S (1-10)')
    amef_occ = fields.Integer(string='AMEF O (1-10)')
    amef_det = fields.Integer(string='AMEF D (1-10)')
    rpn = fields.Integer(compute='_compute_rpn', store=True, string='RPN')

    control_ids = fields.One2many('amunet.amef.control', 'line_id', string='Controles de riesgo')

    # Riesgo residual
    severidad_residual = fields.Selection(NIVEL_SELECTION, string='Severidad residual')
    probabilidad_residual = fields.Selection(NIVEL_SELECTION, string='Probabilidad residual')
    indice_residual = fields.Integer(compute='_compute_riesgo', store=True, string='Índice residual')
    aceptabilidad_residual = fields.Selection(
        ACEPT_SELECTION, compute='_compute_riesgo', store=True, string='Aceptabilidad residual')

    justificacion = fields.Text(string='Justificación beneficio/riesgo (si residual no aceptable)')
    estado_linea = fields.Selection([
        ('abierto', 'Abierto'),
        ('controlado', 'Controlado'),
        ('cerrado', 'Cerrado'),
    ], string='Estado', default='abierto')

    @api.depends('severidad_inicial', 'probabilidad_inicial',
                 'severidad_residual', 'probabilidad_residual')
    def _compute_riesgo(self):
        for l in self:
            ii = int(l.severidad_inicial or 0) * int(l.probabilidad_inicial or 0)
            ir = int(l.severidad_residual or 0) * int(l.probabilidad_residual or 0)
            l.indice_inicial = ii
            l.indice_residual = ir
            l.aceptabilidad_inicial = _acceptability(ii)
            l.aceptabilidad_residual = _acceptability(ir)

    @api.depends('amef_sev', 'amef_occ', 'amef_det')
    def _compute_rpn(self):
        for l in self:
            l.rpn = (l.amef_sev or 0) * (l.amef_occ or 0) * (l.amef_det or 0)

    @api.constrains('amef_sev', 'amef_occ', 'amef_det')
    def _check_amef_scale(self):
        for l in self:
            for v in (l.amef_sev, l.amef_occ, l.amef_det):
                if v and not (1 <= v <= 10):
                    raise ValidationError(_('Las escalas AMEF S/O/D deben estar entre 1 y 10.'))

    def _check_parent_editable(self):
        if self.env.context.get(INTERNAL_CTX):
            return
        for l in self:
            if l.amef_id.state in ('approved', 'archived'):
                raise UserError(_('El AMEF está aprobado; sus líneas son inmutables. Crea una nueva versión.'))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._check_parent_editable()
        return records

    def write(self, vals):
        self._check_parent_editable()
        return super().write(vals)

    def unlink(self):
        self._check_parent_editable()
        return super().unlink()


class AmunetAmefControl(models.Model):
    _name = 'amunet.amef.control'
    _description = 'Medida de Control de Riesgo (ISO 14971)'
    _order = 'line_id, sequence, id'

    line_id = fields.Many2one('amunet.amef.line', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    descripcion = fields.Char(string='Medida de control', required=True)
    tipo_control = fields.Selection([
        ('diseno_seguro', 'Diseño inherentemente seguro'),
        ('medida_protectora', 'Medida protectora'),
        ('info_seguridad', 'Información de seguridad'),
    ], string='Tipo de control (jerarquía 14971)', required=True, default='medida_protectora')
    responsable_id = fields.Many2one('res.users', string='Responsable')
    fecha = fields.Date(string='Fecha')
    document_id = fields.Many2one('amunet.documento', string='PNO / Instructivo / Especificación')
    verif_implementacion = fields.Boolean(string='Implementación verificada')
    fecha_implementacion = fields.Date(string='Fecha verif. implementación')
    verif_efectividad = fields.Boolean(string='Efectividad verificada')
    fecha_efectividad = fields.Date(string='Fecha verif. efectividad')
    notas = fields.Text(string='Notas')

    def _check_parent_editable(self):
        if self.env.context.get(INTERNAL_CTX):
            return
        for c in self:
            if c.line_id.amef_id.state in ('approved', 'archived'):
                raise UserError(_('El AMEF está aprobado; sus controles son inmutables. Crea una nueva versión.'))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._check_parent_editable()
        return records

    def write(self, vals):
        self._check_parent_editable()
        return super().write(vals)

    def unlink(self):
        self._check_parent_editable()
        return super().unlink()
