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
    motivo = fields.Text(string='Motivo del cambio', required=True, tracking=True)
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
