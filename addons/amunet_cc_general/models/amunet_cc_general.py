# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AmunetCCGeneralActividad(models.Model):
    _name = 'amunet.cc.general.actividad'
    _description = 'Actividad del plan de implementación'
    _order = 'sequence, id'

    cc_id          = fields.Many2one('amunet.cc.general', required=True,
                                     ondelete='cascade', index=True)
    sequence       = fields.Integer(default=10)
    actividad      = fields.Char(string='Actividad')
    responsable_id = fields.Many2one('res.users', string='Responsable')
    firma_enterado_id  = fields.Many2one('res.users', string='Enterado', readonly=True)
    fecha_enterado     = fields.Datetime(string='Fecha enterado', readonly=True)
    recursos       = fields.Char(string='Recursos necesarios')
    fecha_inicio   = fields.Date(string='Fecha de inicio')
    fecha_termino  = fields.Date(string='Fecha de término')
    verifico_id        = fields.Many2one('res.users', string='Verifica')
    firma_verifico_id  = fields.Many2one('res.users', string='Firmó verificación', readonly=True)
    fecha_verificacion = fields.Datetime(string='Fecha de verificación', readonly=True)

    estado_enterado = fields.Selection([
        ('enterado',  'Enterado'),
        ('pendiente', 'Pendiente'),
    ], string='Estado enterado', compute='_compute_estado_enterado')

    @api.depends('firma_enterado_id')
    def _compute_estado_enterado(self):
        for r in self:
            r.estado_enterado = 'enterado' if r.firma_enterado_id else 'pendiente'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.responsable_id:
                record._notificar_responsable()
        return records

    def write(self, vals):
        old = {r.id: r.responsable_id.id for r in self}
        result = super().write(vals)
        if 'responsable_id' in vals:
            for record in self:
                nuevo = record.responsable_id.id
                if nuevo and nuevo != old.get(record.id):
                    record._notificar_responsable()
        return result

    def _notificar_responsable(self):
        self.ensure_one()
        if not self.responsable_id or not self.cc_id:
            return
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = '%s/odoo/control-de-cambios/%s' % (base_url, self.cc_id.id)
        self.cc_id.message_post(
            body=_(
                'Hola <b>%s</b>, se te ha asignado la responsabilidad de la actividad '
                '<b>"%s"</b> en el control de cambios <b>%s</b>.<br/>'
                'Por favor ingresa al sistema y firma de enterado: '
                '<a href="%s">%s</a>'
            ) % (
                self.responsable_id.name,
                self.actividad or 'Sin nombre',
                self.cc_id.name,
                url, url,
            ),
            partner_ids=[self.responsable_id.partner_id.id],
            subtype_xmlid='mail.mt_comment',
        )

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_enterado':    _('Firma de enterado'),
            '_signature_verificacion': _('Verificación de actividad'),
        }

    def action_firmar_enterado(self):
        self.ensure_one()
        if self.firma_enterado_id:
            raise UserError(_('Ya está registrada la firma de enterado.'))
        if self.responsable_id and self.responsable_id != self.env.user:
            raise UserError(_('Solo %s puede firmar de enterado.') % self.responsable_id.name)
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_enterado', _('Firma de enterado'),
            _('Actividad: %s') % (self.actividad or ''))

    def _signature_enterado(self):
        self.ensure_one()
        self.write({
            'firma_enterado_id': self.env.user.id,
            'fecha_enterado': fields.Datetime.now(),
        })

    def action_firmar_verificacion(self):
        self.ensure_one()
        if self.firma_verifico_id:
            raise UserError(_('Esta actividad ya fue verificada.'))
        if self.responsable_id and self.responsable_id == self.env.user:
            raise UserError(_('El responsable de realizar la actividad no puede firmar su propia verificación.'))
        if self.verifico_id and self.verifico_id != self.env.user:
            raise UserError(_('Solo %s puede verificar esta actividad.') % self.verifico_id.name)
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_verificacion', _('Verificación de actividad'),
            _('Actividad: %s') % (self.actividad or ''))

    def _signature_verificacion(self):
        self.ensure_one()
        self.write({
            'firma_verifico_id': self.env.user.id,
            'fecha_verificacion': fields.Datetime.now(),
        })


class AmunetCCGeneral(models.Model):
    _name = 'amunet.cc.general'
    _description = 'Control de Cambios General'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_solicitud desc, id desc'

    name = fields.Char(string='Folio', required=True, copy=False,
                       readonly=True, default='Nuevo')
    state = fields.Selection([
        ('borrador',  'Borrador'),
        ('pendiente', 'En revisión'),
        ('aceptado',  'Autorizado'),
        ('rechazado', 'Rechazado'),
        ('cerrado',   'Cerrado'),
    ], string='Estado', default='borrador', tracking=True)

    # ── Encabezado ──────────────────────────────────────────────
    fecha_solicitud = fields.Date(string='Fecha de solicitud',
                                  default=fields.Date.today, tracking=True)
    solicitante_id  = fields.Many2one('res.users', string='Solicitante',
                                      default=lambda self: self.env.user,
                                      tracking=True)
    departamento    = fields.Char(string='Departamento / Área', tracking=True)

    # ── Sección 1: Tipo y descripción ────────────────────────────
    tipo_procedimiento = fields.Boolean(string='Instrucciones')
    tipo_formula       = fields.Boolean(string='Fórmula / Insumo')
    tipo_proveedor     = fields.Boolean(string='Proveedor')
    tipo_instalacion   = fields.Boolean(string='Instalación / Área')
    tipo_equipo        = fields.Boolean(string='Equipo')
    tipo_manual        = fields.Boolean(string='Manual')
    tipo_formato       = fields.Boolean(string='Formato')
    tipo_otro          = fields.Boolean(string='Otro')
    tipo_otro_desc     = fields.Char(string='Especifica (Otro)')

    estado_actual    = fields.Text(string='Estado actual (¿Cómo está ahora?)')
    estado_propuesto = fields.Text(string='Estado propuesto (¿Cómo debe quedar?)')
    justificacion    = fields.Text(string='Justificación del cambio')

    # ── Sección 2: Firmas de autorización ────────────────────────
    elaboro_id       = fields.Many2one('res.users', string='Elaboró')
    firma_elaboro_id = fields.Many2one('res.users', string='Firma (Elaboró)', readonly=True)
    fecha_elaboro    = fields.Datetime(string='Fecha firma (Elaboró)', readonly=True)

    reviso_id        = fields.Many2one('res.users', string='Revisó')
    firma_reviso_id  = fields.Many2one('res.users', string='Firma (Revisó)', readonly=True)
    fecha_reviso     = fields.Datetime(string='Fecha firma (Revisó)', readonly=True)
    vb_reviso        = fields.Selection([('si', 'Sí'), ('no', 'No')],
                                         string='Visto bueno (Revisó)', readonly=True)

    aprobo_id        = fields.Many2one('res.users', string='Aprobó')
    firma_aprobo_id  = fields.Many2one('res.users', string='Firma (Aprobó)', readonly=True)
    fecha_aprobo     = fields.Datetime(string='Fecha firma (Aprobó)', readonly=True)
    vb_aprobo        = fields.Selection([('si', 'Sí'), ('no', 'No')],
                                         string='¿Se autoriza?', readonly=True)
    motivo_rechazo   = fields.Text(string='Motivo del rechazo')

    # ── Sección 3: Plan de implementación ────────────────────────
    fecha_propuesta  = fields.Date(string='Fecha propuesta para el cambio')
    lote_aplicacion  = fields.Char(string='Lote / Fecha a partir de la cual aplica')
    acciones_previas = fields.Text(string='Acciones previas necesarias')

    # ── Implementación y seguimiento ─────────────────────────────
    actividades_ids = fields.One2many('amunet.cc.general.actividad', 'cc_id',
                                       string='Actividades')

    # ── Sección 4: Verificación y cierre ─────────────────────────
    fecha_implementacion    = fields.Date(string='Fecha de implementación real')
    responsable_cierre_id   = fields.Many2one('res.users', string='Responsable del cierre')
    resultados_verificacion = fields.Text(string='Resultados de la verificación')
    evidencia_anexa         = fields.Html(string='Evidencia anexa')
    nueva_version           = fields.Char(string='Nueva versión del documento (si aplica)')
    firma_cierre_id         = fields.Many2one('res.users', string='Firma de cierre (Calidad)',
                                               readonly=True)
    fecha_cierre_firma      = fields.Datetime(string='Fecha firma de cierre', readonly=True)

    adjunto_ids = fields.Many2many('ir.attachment', string='Archivos adjuntos')

    # ── Secuencia ────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = (self.env['ir.sequence']
                                .next_by_code('amunet.solicitud.cambio') or 'Nuevo')
        return super().create(vals_list)

    # ── Acciones de flujo ────────────────────────────────────────
    def action_enviar(self):
        for r in self:
            if r.state != 'borrador':
                raise UserError(_('Solo puedes enviar un registro en borrador.'))
            if not r.estado_actual or not r.estado_propuesto or not r.justificacion:
                raise UserError(_('Completa al menos: Estado actual, Estado propuesto y Justificación.'))
            if not r.aprobo_id:
                raise UserError(_('Indica quién debe autorizar este control de cambios antes de enviarlo.'))
            r.state = 'pendiente'
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = '%s/odoo/control-de-cambios/%s' % (base_url, r.id)
            partners = r.aprobo_id.partner_id
            if r.reviso_id:
                partners |= r.reviso_id.partner_id
            r.message_post(
                body=_(
                    'El control de cambios <b>%s</b> requiere tu autorización.<br/>'
                    '<a href="%s">Haz clic aquí para revisarlo.</a>'
                ) % (r.name, url),
                partner_ids=partners.ids,
                subtype_xmlid='mail.mt_comment',
            )

    def action_aceptar(self):
        for r in self:
            if r.state != 'pendiente':
                raise UserError(_('Solo puedes autorizar registros en revisión.'))
            r.write({'state': 'aceptado',
                     'firma_aprobo_id': self.env.user.id,
                     'fecha_aprobo': fields.Datetime.now(),
                     'vb_aprobo': 'si'})

    def action_rechazar(self):
        for r in self:
            if r.state != 'pendiente':
                raise UserError(_('Solo puedes rechazar registros en revisión.'))
            if not r.motivo_rechazo:
                raise UserError(_('Escribe el motivo del rechazo antes de rechazar.'))
            r.write({'state': 'rechazado',
                     'firma_aprobo_id': self.env.user.id,
                     'fecha_aprobo': fields.Datetime.now(),
                     'vb_aprobo': 'no'})

    def action_cerrar(self):
        for r in self:
            if r.state != 'aceptado':
                raise UserError(_('Solo puedes cerrar un registro autorizado.'))
            r.state = 'cerrado'

    # ── Firmas con PIN ───────────────────────────────────────────
    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_elaboro': _('Firma de quien elaboró'),
            '_signature_reviso':  _('Firma de quien revisó'),
            '_signature_cierre':  _('Firma de cierre'),
        }

    def _abrir_firma(self, method_name, label):
        self.ensure_one()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, method_name, label,
            _('Control de cambios: %s') % (self.name or ''))

    def action_firmar_elaboro(self):
        self.ensure_one()
        if self.firma_elaboro_id:
            raise UserError(_('Ya se registró esta firma.'))
        if self.elaboro_id and self.elaboro_id != self.env.user:
            raise UserError(_('Solo %s puede firmar en este espacio.') % self.elaboro_id.name)
        return self._abrir_firma('_signature_elaboro', _('Firma de quien elaboró'))

    def _signature_elaboro(self):
        self.ensure_one()
        self.write({'firma_elaboro_id': self.env.user.id,
                    'fecha_elaboro': fields.Datetime.now()})
        self._message_log(body=_('<p><b>%s</b> firmó como Elaboró.</p>') % self.env.user.name)

    def action_firmar_reviso(self):
        self.ensure_one()
        if self.firma_reviso_id:
            raise UserError(_('Ya se registró esta firma.'))
        if self.reviso_id and self.reviso_id != self.env.user:
            raise UserError(_('Solo %s puede firmar en este espacio.') % self.reviso_id.name)
        return self._abrir_firma('_signature_reviso', _('Firma de quien revisó'))

    def _signature_reviso(self):
        self.ensure_one()
        self.write({'firma_reviso_id': self.env.user.id,
                    'fecha_reviso': fields.Datetime.now(),
                    'vb_reviso': 'si'})
        self._message_log(body=_('<p><b>%s</b> firmó como Revisó.</p>') % self.env.user.name)

    def action_firmar_cierre(self):
        self.ensure_one()
        if self.firma_cierre_id:
            raise UserError(_('Ya se registró la firma de cierre.'))
        return self._abrir_firma('_signature_cierre', _('Firma de cierre'))

    def _signature_cierre(self):
        self.ensure_one()
        self.write({'firma_cierre_id': self.env.user.id,
                    'fecha_cierre_firma': fields.Datetime.now()})
        self._message_log(body=_('<p><b>%s</b> firmó el cierre.</p>') % self.env.user.name)

    def action_descartar(self):
        for r in self:
            if r.state != 'borrador':
                raise UserError(_('Solo puedes eliminar un registro en borrador.'))
        self.unlink()
        return {'type': 'ir.actions.client', 'tag': 'history_back'}
