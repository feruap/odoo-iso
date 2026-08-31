# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError

USER_GROUP = 'amunet_revision_direccion.group_review_user'
APPROVER_GROUP = 'amunet_revision_direccion.group_review_approver'
INTERNAL_CTX = '_review_internal'

INPUT_TYPES = [
    ('auditorias', 'Resultados de auditorías'),
    ('retroalimentacion', 'Retroalimentación / quejas de clientes'),
    ('procesos', 'Desempeño de procesos y conformidad de producto'),
    ('capa', 'Estado de acciones correctivas y preventivas (CAPA)'),
    ('seguimiento', 'Seguimiento de revisiones previas'),
    ('cambios', 'Cambios que afectan el SGC'),
    ('regulatorio', 'Nuevos requisitos regulatorios'),
    ('mejora', 'Recomendaciones de mejora'),
]


class AmunetManagementReview(models.Model):
    _name = 'amunet.management.review'
    _description = 'Revisión por la Dirección (ISO 13485 §5.6)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, id desc'

    name = fields.Char(string='Título', required=True, tracking=True)
    code = fields.Char(string='Código', required=True, index=True, tracking=True)
    fecha = fields.Date(string='Fecha de la reunión', default=fields.Date.context_today, tracking=True)
    periodo = fields.Char(string='Periodo revisado')
    participantes = fields.Text(string='Participantes')
    document_id = fields.Many2one('amunet.documento', string='PNO / Documento (PNOAD-001)')

    input_ids = fields.One2many('amunet.management.review.input', 'review_id', string='Entradas')
    action_ids = fields.One2many('amunet.management.review.action', 'review_id', string='Acuerdos y acciones')

    conclusion = fields.Text(string='Conclusiones / salidas de la revisión')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('in_review', 'En revisión'),
        ('approved', 'Aprobada'),
        ('archived', 'Archivada'),
    ], string='Estado', default='draft', required=True, tracking=True)

    revisa_id = fields.Many2one('res.users', string='Revisado por', readonly=True)
    fecha_revisa = fields.Datetime(string='Fecha revisión', readonly=True)
    aprueba_id = fields.Many2one('res.users', string='Aprobada por (Dirección)', readonly=True)
    fecha_aprueba = fields.Datetime(string='Fecha aprobación', readonly=True)

    action_open_count = fields.Integer(compute='_compute_counts', string='Acciones abiertas')

    _code_uniq = models.Constraint('unique(code)', 'El código de la revisión debe ser único.')

    SIGN_FIELDS = {'state', 'revisa_id', 'fecha_revisa', 'aprueba_id', 'fecha_aprueba'}

    @api.depends('action_ids.estado')
    def _compute_counts(self):
        for r in self:
            r.action_open_count = len(r.action_ids.filtered(lambda a: a.estado == 'abierto'))

    def write(self, vals):
        if not self.env.context.get(INTERNAL_CTX):
            bad = self.SIGN_FIELDS.intersection(vals.keys())
            if bad:
                raise UserError(_('Estos campos solo se actualizan por el flujo de firma: %s')
                                % ', '.join(sorted(bad)))
            mail_fields = {'message_main_attachment_id', 'message_ids',
                           'message_follower_ids', 'activity_ids'}
            for r in self:
                if r.state in ('approved', 'archived'):
                    illegal = set(vals.keys()) - mail_fields
                    if illegal:
                        raise UserError(_('La revisión "%s" está %s y es inmutable.')
                                        % (r.name, r.state))
        return super().write(vals)

    def action_submit_review(self):
        for r in self:
            if r.state != 'draft':
                raise UserError(_('Solo se envían a revisión las que están en borrador.'))
            if not r.input_ids:
                raise UserError(_('Captura las entradas de la revisión antes de continuar.'))
            r.with_context(**{INTERNAL_CTX: True}).write({'state': 'in_review'})

    def action_open_sign(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'name': _('Firmar revisión'),
            'res_model': 'amunet.review.sign.wizard', 'view_mode': 'form',
            'target': 'new', 'context': {'default_review_id': self.id},
        }

    def _do_sign(self, role):
        self.ensure_one()
        is_approver = self.env.su or self.env.user.has_group(APPROVER_GROUP)
        if role == 'revisa':
            if self.state != 'in_review':
                raise UserError(_('La revisión debe estar en revisión.'))
            self.with_context(**{INTERNAL_CTX: True}).write({
                'revisa_id': self.env.user.id, 'fecha_revisa': fields.Datetime.now()})
            return True
        if not is_approver:
            raise AccessError(_('Solo la Dirección puede aprobar la revisión.'))
        if self.state != 'in_review':
            raise UserError(_('La revisión debe estar en revisión antes de aprobar.'))
        if not self.conclusion:
            raise UserError(_('Documenta las conclusiones/salidas antes de aprobar.'))
        self.with_context(**{INTERNAL_CTX: True}).write({
            'state': 'approved', 'aprueba_id': self.env.user.id,
            'fecha_aprueba': fields.Datetime.now()})
        return True

    def action_archive_review(self):
        if not (self.env.su or self.env.user.has_group(APPROVER_GROUP)):
            raise AccessError(_('Solo un aprobador puede archivar.'))
        self.with_context(**{INTERNAL_CTX: True}).write({'state': 'archived'})


class AmunetManagementReviewInput(models.Model):
    _name = 'amunet.management.review.input'
    _description = 'Entrada de revisión por la dirección'
    _order = 'review_id, sequence, id'

    review_id = fields.Many2one('amunet.management.review', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    tipo = fields.Selection(INPUT_TYPES, string='Tipo de entrada', required=True)
    descripcion = fields.Text(string='Descripción / hallazgo', required=True)

    def _check_editable(self):
        if self.env.context.get(INTERNAL_CTX):
            return
        for r in self:
            if r.review_id.state in ('approved', 'archived'):
                raise UserError(_('La revisión está aprobada; sus entradas son inmutables.'))

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


class AmunetManagementReviewAction(models.Model):
    _name = 'amunet.management.review.action'
    _description = 'Acuerdo / acción de revisión por la dirección'
    _order = 'review_id, sequence, id'

    review_id = fields.Many2one('amunet.management.review', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    descripcion = fields.Char(string='Acuerdo / acción', required=True)
    responsable_id = fields.Many2one('res.users', string='Responsable')
    fecha_objetivo = fields.Date(string='Fecha objetivo')
    estado = fields.Selection([('abierto', 'Abierto'), ('cerrado', 'Cerrado')],
                              string='Estado', default='abierto')
    capa_id = fields.Many2one('amunet.quality.capa', string='CAPA relacionada')
    notas = fields.Text(string='Notas / seguimiento')

    def _check_editable(self):
        if self.env.context.get(INTERNAL_CTX):
            return
        for r in self:
            if r.review_id.state == 'archived':
                raise UserError(_('La revisión está archivada; sus acciones son inmutables.'))

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        recs._check_editable()
        return recs

    def write(self, vals):
        # Las acciones se pueden seguir gestionando (cerrar) tras aprobar; solo se bloquean al archivar.
        self._check_editable()
        return super().write(vals)

    def unlink(self):
        for r in self:
            if r.review_id.state in ('approved', 'archived'):
                raise UserError(_('No se pueden eliminar acciones de una revisión aprobada.'))
        return super().unlink()
