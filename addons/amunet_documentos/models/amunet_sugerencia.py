# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


SECCION_SELECTION = [
    ('objetivo', 'Objetivo'),
    ('alcance', 'Alcance'),
    ('introduccion', 'Introduccion'),
    ('mision_vision', 'Mision y Vision'),
    ('responsabilidades', 'Responsabilidades'),
    ('organigrama', 'Organigrama'),
    ('terminos_definiciones', 'Terminos y definiciones'),
    ('condiciones_generales', 'Condiciones generales'),
    ('formatos_derivados', 'Formatos derivados'),
    ('referencias', 'Referencias bibliograficas'),
    ('anexos', 'Anexos'),
    ('contenido_libre', 'Contenido libre (otros)'),
]

SECCION_FIELD_MAP = {
    'objetivo': 'seccion_objetivo',
    'alcance': 'seccion_alcance',
    'introduccion': 'seccion_introduccion',
    'mision_vision': 'seccion_mision_vision',
    'responsabilidades': 'seccion_responsabilidades',
    'organigrama': 'seccion_organigrama',
    'terminos_definiciones': 'seccion_terminos_definiciones',
    'condiciones_generales': 'seccion_condiciones_generales',
    'formatos_derivados': 'seccion_formatos_derivados',
    'referencias': 'seccion_referencias',
    'anexos': 'seccion_anexos',
    'contenido_libre': 'contenido_html',
}


class AmunetSugerenciaComite(models.Model):
    _name = 'amunet.sugerencia.comite'
    _description = 'Integrante del comité técnico en control de cambios'
    _order = 'sequence, id'

    sugerencia_id    = fields.Many2one(
        'amunet.documento.sugerencia', required=True, ondelete='cascade')
    sequence         = fields.Integer(default=10)
    area             = fields.Char(string='Área')
    fecha            = fields.Date(string='Fecha')
    nombre_id        = fields.Many2one('res.users', string='Nombre')
    usuario_firma_id = fields.Many2one(
        'res.users', string='Firmado por', readonly=True, tracking=True)
    fecha_firma      = fields.Date(string='Fecha de firma', readonly=True, tracking=True)

    @api.onchange('nombre_id')
    def _onchange_nombre_id(self):
        if self.nombre_id:
            try:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', self.nombre_id.id)], limit=1)
                if employee and employee.department_id:
                    self.area = employee.department_id.name
            except Exception:
                pass

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_firmar_comite': _('Firma de comité técnico'),
        }

    def action_firmar_comite(self):
        self.ensure_one()
        if not self.env.user.has_group('amunet_documentos.group_comite_tecnico'):
            raise UserError(_('Solo los integrantes del comité técnico pueden firmar aquí.'))
        if self.usuario_firma_id:
            raise UserError(_('Este integrante ya firmó el control de cambios.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self,
            '_signature_firmar_comite',
            _('Firma de comité técnico'),
            _('Aprobación del control de cambios: %s') % self.sugerencia_id.name,
        )

    def _signature_firmar_comite(self):
        self.ensure_one()
        if not self.env.user.has_group('amunet_documentos.group_comite_tecnico'):
            raise UserError(_('Solo los integrantes del comité técnico pueden firmar aquí.'))
        self.write({
            'usuario_firma_id': self.env.user.id,
            'fecha_firma': fields.Date.today(),
        })
        self.sugerencia_id.message_post(
            body=_('<p><b>%s</b> firmó como integrante del comité técnico (área: %s).</p>')
                 % (self.env.user.name, self.area or ''),
        )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for r in records:
            if r.nombre_id and r.sugerencia_id:
                r.sugerencia_id.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Firma requerida — comité técnico'),
                    note=_('<p>Fuiste agregado al comité técnico del control de cambios '
                           '<b>%s</b>. Abre el registro y usa el botón <b>Firmar</b> '
                           'para registrar tu aprobación con PIN.</p>')
                          % r.sugerencia_id.name,
                    user_id=r.nombre_id.id,
                )
        return records


class AmunetDocumentoSugerencia(models.Model):
    _name = 'amunet.documento.sugerencia'
    _description = 'Sugerencia de cambio en documento controlado'
    _inherit = ['mail.thread']
    _order = 'fecha_creacion desc'

    name = fields.Char(string='Resumen', compute='_compute_name', store=True)
    documento_id = fields.Many2one(
        'amunet.documento', required=True, ondelete='cascade', tracking=True)
    documento_codigo = fields.Char(related='documento_id.codigo',
                                   string='Codigo del documento', store=True)
    seccion = fields.Selection(
        SECCION_SELECTION, string='Seccion a cambiar', required=True, tracking=True)
    texto_original = fields.Html(
        string='Texto actual', sanitize=True, sanitize_tags=False, readonly=True)
    texto_propuesto = fields.Html(
        string='Texto propuesto', sanitize=True, sanitize_tags=False, required=True)
    motivo = fields.Text(string='Justificación del cambio', required=True, tracking=True)

    tipo_cambio = fields.Selection([
        ('planeado',    'Planeado'),
        ('no_planeado', 'No planeado'),
    ], string='Tipo de cambio', tracking=True)

    # Alcance del cambio
    alcance_material       = fields.Boolean(string='Material')
    alcance_documentos     = fields.Boolean(string='Documentos')
    alcance_equipo         = fields.Boolean(string='Equipos')
    alcance_procesos       = fields.Boolean(string='Procesos')
    alcance_estructura     = fields.Boolean(string='Infraestructura')
    alcance_sgc            = fields.Boolean(string='SGC')

    comite_ids = fields.One2many(
        'amunet.sugerencia.comite', 'sugerencia_id',
        string='Comité técnico')
    comite_users_ids = fields.Many2many(
        'res.users', compute='_compute_comite_users_ids')

    def _compute_comite_users_ids(self):
        group = self.env.ref(
            'amunet_documentos.group_comite_tecnico', raise_if_not_found=False)
        users = group.users if group else self.env['res.users']
        for r in self:
            r.comite_users_ids = users

    # Firmas de aplicación del cambio
    realizo_id       = fields.Many2one('res.users', string='Realizó')
    firma_realizo_id = fields.Many2one('res.users', string='Firmó (realizó)', readonly=True)
    fecha_realizo    = fields.Date(string='Fecha', readonly=True)
    reviso_id        = fields.Many2one('res.users', string='Revisó')
    firma_reviso_id  = fields.Many2one('res.users', string='Firmó (revisó)', readonly=True)
    fecha_reviso     = fields.Date(string='Fecha', readonly=True)
    aprobo_id        = fields.Many2one('res.users', string='Aprobó')
    firma_aprobo_id  = fields.Many2one('res.users', string='Firmó (aprobó)', readonly=True)
    fecha_aprobo     = fields.Date(string='Fecha', readonly=True)

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_realizo':  _('Firma quien realizó el cambio'),
            '_signature_reviso':   _('Firma quien revisó el cambio'),
            '_signature_aprobo':   _('Firma quien aprobó la aplicación del cambio'),
        }

    def _abrir_firma(self, method_name, label):
        self.ensure_one()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, method_name, label,
            _('Control de cambios: %s') % (self.name or ''))

    def action_firmar_realizo(self):
        self.ensure_one()
        if self.firma_realizo_id:
            raise UserError(_('Ya se registró la firma de quien realizó el cambio.'))
        if self.realizo_id and self.realizo_id != self.env.user:
            raise UserError(_('Solo %s puede firmar en este espacio.') % self.realizo_id.name)
        return self._abrir_firma('_signature_realizo', _('Firma quien realizó el cambio'))

    def _signature_realizo(self):
        self.ensure_one()
        self.write({'firma_realizo_id': self.env.user.id, 'fecha_realizo': fields.Date.today()})
        self.message_post(body=_('<p><b>%s</b> registró su firma como quien realizó el cambio.</p>') % self.env.user.name)

    def action_firmar_reviso(self):
        self.ensure_one()
        if self.firma_reviso_id:
            raise UserError(_('Ya se registró la firma de quien revisó el cambio.'))
        if self.reviso_id and self.reviso_id != self.env.user:
            raise UserError(_('Solo %s puede firmar en este espacio.') % self.reviso_id.name)
        return self._abrir_firma('_signature_reviso', _('Firma quien revisó el cambio'))

    def _signature_reviso(self):
        self.ensure_one()
        self.write({'firma_reviso_id': self.env.user.id, 'fecha_reviso': fields.Date.today()})
        self.message_post(body=_('<p><b>%s</b> registró su firma como quien revisó el cambio.</p>') % self.env.user.name)

    def action_firmar_aprobo(self):
        self.ensure_one()
        if self.firma_aprobo_id:
            raise UserError(_('Ya se registró la firma de quien aprobó el cambio.'))
        if self.aprobo_id and self.aprobo_id != self.env.user:
            raise UserError(_('Solo %s puede firmar en este espacio.') % self.aprobo_id.name)
        return self._abrir_firma('_signature_aprobo', _('Firma quien aprobó la aplicación del cambio'))

    def _signature_aprobo(self):
        self.ensure_one()
        self.write({'firma_aprobo_id': self.env.user.id, 'fecha_aprobo': fields.Date.today()})
        self.message_post(body=_('<p><b>%s</b> registró su firma como quien aprobó la aplicación del cambio.</p>') % self.env.user.name)

    state = fields.Selection([
        ('pendiente', 'Pendiente de decision'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    ], string='Estado', default='pendiente', tracking=True)
    creado_por_id = fields.Many2one(
        'res.users', string='Propuesto por',
        default=lambda self: self.env.user, readonly=True, tracking=True)
    fecha_creacion = fields.Datetime(
        string='Fecha de propuesta', default=fields.Datetime.now, readonly=True)
    decidido_por_id = fields.Many2one(
        'res.users', string='Decidido por', readonly=True, tracking=True)
    fecha_decision = fields.Datetime(string='Fecha de decision', readonly=True)
    motivo_rechazo = fields.Text(string='Motivo del rechazo', tracking=True)

    @api.depends('documento_codigo', 'seccion', 'state')
    def _compute_name(self):
        seccion_dict = dict(SECCION_SELECTION)
        for r in self:
            r.name = '%s - %s' % (r.documento_codigo or '?',
                                  seccion_dict.get(r.seccion, '?'))

    @api.onchange('seccion', 'documento_id')
    def _onchange_seccion_prellenar(self):
        for r in self:
            if r.documento_id and r.seccion:
                field = SECCION_FIELD_MAP.get(r.seccion)
                if field:
                    actual = getattr(r.documento_id, field) or ''
                    r.texto_original = actual
                    if not r.texto_propuesto:
                        r.texto_propuesto = actual

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('documento_id') and vals.get('seccion') and not vals.get('texto_original'):
                doc = self.env['amunet.documento'].browse(vals['documento_id'])
                field = SECCION_FIELD_MAP.get(vals['seccion'])
                if field:
                    vals['texto_original'] = getattr(doc, field) or ''
        records = super().create(vals_list)
        for r in records:
            if r.documento_id.elabora_id:
                r.documento_id.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Sugerencia de cambio en %s') % r.documento_id.codigo,
                    note=_(
                        '<p>%s sugiere un cambio en la seccion <b>%s</b> del documento '
                        '<b>%s</b>.</p><p><b>Motivo:</b> %s</p>'
                        '<p>Abre el documento y ve a la pestana "Sugerencias" para decidir.</p>'
                    ) % (r.creado_por_id.name,
                         dict(SECCION_SELECTION).get(r.seccion, r.seccion),
                         r.documento_id.codigo, r.motivo),
                    user_id=r.documento_id.elabora_id.id,
                )
            r.documento_id.message_post(
                body=_(
                    '<p><b>Nueva sugerencia</b> de %s en la seccion <b>%s</b>.</p>'
                    '<p><b>Motivo:</b> %s</p>'
                ) % (r.creado_por_id.name,
                     dict(SECCION_SELECTION).get(r.seccion, r.seccion),
                     r.motivo),
                subject=_('Sugerencia de cambio'),
            )
        return records

    def action_aceptar(self):
        for r in self:
            if r.state != 'pendiente':
                raise UserError(_('Esta sugerencia ya tiene decision (%s).') % r.state)
            if r.documento_id.elabora_id \
                    and r.documento_id.elabora_id.id != self.env.user.id \
                    and not self.env.user.has_group('amunet_documentos.group_documentos_manager'):
                raise UserError(_(
                    'Solo el elaborador del documento (%s) puede aceptar o rechazar sugerencias.'
                ) % r.documento_id.elabora_id.name)
            if r.documento_id.state == 'vigente':
                raise UserError(_(
                    'No se puede aplicar una sugerencia a un documento Vigente. '
                    'Pasalo a borrador (via nueva version) primero.'))
            field = SECCION_FIELD_MAP.get(r.seccion)
            if field:
                r.documento_id.sudo().write({field: r.texto_propuesto})
            r.write({
                'state': 'aceptada',
                'decidido_por_id': self.env.user.id,
                'fecha_decision': fields.Datetime.now(),
            })
            if r.creado_por_id:
                r.documento_id.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Sugerencia aceptada en %s') % r.documento_id.codigo,
                    note=_(
                        '<p>%s acepto tu sugerencia en la seccion <b>%s</b>.</p>'
                    ) % (self.env.user.name,
                         dict(SECCION_SELECTION).get(r.seccion, r.seccion)),
                    user_id=r.creado_por_id.id,
                )
            r.documento_id.message_post(
                body=_(
                    '<p><b>Sugerencia aceptada</b> por %s en la seccion <b>%s</b>.</p>'
                ) % (self.env.user.name,
                     dict(SECCION_SELECTION).get(r.seccion, r.seccion)),
            )

    def action_rechazar(self):
        for r in self:
            if r.state != 'pendiente':
                raise UserError(_('Esta sugerencia ya tiene decision (%s).') % r.state)
            if not (r.motivo_rechazo or '').strip():
                raise UserError(_('Indica el motivo del rechazo.'))
            if r.documento_id.elabora_id \
                    and r.documento_id.elabora_id.id != self.env.user.id \
                    and not self.env.user.has_group('amunet_documentos.group_documentos_manager'):
                raise UserError(_(
                    'Solo el elaborador del documento (%s) puede aceptar o rechazar sugerencias.'
                ) % r.documento_id.elabora_id.name)
            r.write({
                'state': 'rechazada',
                'decidido_por_id': self.env.user.id,
                'fecha_decision': fields.Datetime.now(),
            })
            if r.creado_por_id:
                r.documento_id.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Sugerencia rechazada en %s') % r.documento_id.codigo,
                    note=_(
                        '<p>%s rechazo tu sugerencia.</p><p><b>Motivo del rechazo:</b> %s</p>'
                    ) % (self.env.user.name, r.motivo_rechazo),
                    user_id=r.creado_por_id.id,
                )
            r.documento_id.message_post(
                body=_(
                    '<p><b>Sugerencia rechazada</b> por %s. <b>Motivo:</b> %s</p>'
                ) % (self.env.user.name, r.motivo_rechazo),
            )
