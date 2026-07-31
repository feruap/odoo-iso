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
                'Hola <b>%s</b>,<br/><br/>'
                'Se te asignó la actividad <b>"%s"</b> en el control de cambios <b>%s</b>.<br/><br/>'
                'Para registrar tu conformidad, abre el control de cambios, localiza tu actividad '
                'y haz clic en el botón <b>"Firmar enterado"</b>.<br/><br/>'
                '<a href="%s">Abrir control de cambios %s</a>'
            ) % (
                self.responsable_id.name,
                self.actividad or 'Sin nombre',
                self.cc_id.name,
                url, self.cc_id.name,
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
        self.cc_id._verificar_implementacion_completa()

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
        self.cc_id._verificar_implementacion_completa()


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
    solicitante_id      = fields.Many2one('res.users', string='Solicitante',
                                          default=lambda self: self.env.user,
                                          tracking=True)
    firma_solicitante_id = fields.Many2one('res.users', string='Firma (Solicitante)', readonly=True)
    fecha_solicitante    = fields.Datetime(string='Fecha firma (Solicitante)', readonly=True)

    departamento    = fields.Selection([
        ('produccion',    'Producción'),
        ('calidad',       'Control de Calidad'),
        ('almacen',       'Almacén'),
        ('rrhh',          'Recursos Humanos'),
        ('documentacion', 'Documentación'),
        ('ensayo',        'Ensayo / Laboratorio'),
        ('mantenimiento', 'Mantenimiento'),
        ('desarrollo',    'Desarrollo'),
        ('direccion',     'Dirección / Gerencia'),
        ('validacion',    'Validación'),
    ], string='Departamento / Área', tracking=True)

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

    estado_actual    = fields.Text(string='Estado actual')
    estado_propuesto = fields.Text(string='Descripción del cambio')
    justificacion    = fields.Text(string='Justificación')

    # ── Sección 2: Firmas de autorización ────────────────────────
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
    implementacion_notificada = fields.Boolean(default=False)
    cierre_notificado         = fields.Boolean(default=False)

    fecha_implementacion    = fields.Date(string='Fecha de implementación real')
    responsable_cierre_id   = fields.Many2one('res.users', string='Responsable del cierre')
    resultados_verificacion = fields.Text(string='Resultados de la verificación')
    evidencia_anexa         = fields.Html(string='Evidencia anexa')
    nueva_version           = fields.Char(string='Nueva versión del documento (si aplica)')
    firma_cierre_id         = fields.Many2one('res.users', string='Firma de cierre',
                                               readonly=True)
    fecha_cierre_firma      = fields.Datetime(string='Fecha firma de cierre', readonly=True)

    # Firmas de cierre (tres bloques)
    cierre_realizo_id       = fields.Many2one('res.users', string='Realizó el control de cambios')
    firma_cierre_realizo_id = fields.Many2one('res.users', string='Firma', readonly=True)
    fecha_cierre_realizo    = fields.Datetime(string='Fecha', readonly=True)

    cierre_reviso_id        = fields.Many2one('res.users', string='Revisó la aplicación')
    firma_cierre_reviso_id  = fields.Many2one('res.users', string='Firma', readonly=True)
    fecha_cierre_reviso     = fields.Datetime(string='Fecha', readonly=True)

    cierre_aprobo_id        = fields.Many2one('res.users', string='Aprobó la aplicación del cambio')
    firma_cierre_aprobo_id  = fields.Many2one('res.users', string='Firma', readonly=True)
    fecha_cierre_aprobo     = fields.Datetime(string='Fecha', readonly=True)

    adjunto_ids = fields.Many2many('ir.attachment', string='Archivos adjuntos')

    # ── Rol del usuario actual ───────────────────────────────────
    is_manager = fields.Boolean(
        compute='_compute_is_manager',
        compute_sudo=False,
    )

    @api.depends_context('uid')
    def _compute_is_manager(self):
        is_mgr = self.env.user.has_group('amunet_cc_general.group_cc_general_manager')
        for rec in self:
            rec.is_manager = is_mgr

    # ── Acción pendiente del usuario actual ──────────────────────
    accion_pendiente_usuario = fields.Char(
        string='Tu acción',
        compute='_compute_accion_pendiente_usuario',
        compute_sudo=False,
    )

    pendientes_para_ids = fields.Many2many(
        'res.users',
        'amunet_cc_pendientes_para_rel',
        'cc_id', 'user_id',
        string='Usuarios con firma pendiente',
        compute='_compute_pendientes_para',
        store=True,
    )

    @api.depends(
        'state',
        'reviso_id', 'firma_reviso_id',
        'cierre_realizo_id', 'firma_cierre_realizo_id',
        'cierre_reviso_id',  'firma_cierre_reviso_id',
        'cierre_aprobo_id',  'firma_cierre_aprobo_id',
        'actividades_ids.responsable_id', 'actividades_ids.firma_enterado_id',
        'actividades_ids.verifico_id',    'actividades_ids.firma_verifico_id',
    )
    def _compute_pendientes_para(self):
        for rec in self:
            if rec.state in ('borrador', 'cerrado', 'rechazado'):
                rec.pendientes_para_ids = [(5,)]
                continue
            user_ids = set()
            if rec.reviso_id and not rec.firma_reviso_id:
                user_ids.add(rec.reviso_id.id)
            for act in rec.actividades_ids:
                if act.responsable_id and not act.firma_enterado_id:
                    user_ids.add(act.responsable_id.id)
                if act.verifico_id and not act.firma_verifico_id:
                    user_ids.add(act.verifico_id.id)
            for campo, firma in [
                ('cierre_realizo_id', 'firma_cierre_realizo_id'),
                ('cierre_reviso_id',  'firma_cierre_reviso_id'),
                ('cierre_aprobo_id',  'firma_cierre_aprobo_id'),
            ]:
                user = rec[campo]
                if user and not rec[firma]:
                    user_ids.add(user.id)
            rec.pendientes_para_ids = [(6, 0, list(user_ids))]

    @api.depends('reviso_id', 'firma_reviso_id',
                 'actividades_ids.responsable_id', 'actividades_ids.firma_enterado_id',
                 'actividades_ids.verifico_id', 'actividades_ids.firma_verifico_id',
                 'cierre_realizo_id', 'firma_cierre_realizo_id',
                 'cierre_reviso_id', 'firma_cierre_reviso_id',
                 'cierre_aprobo_id', 'firma_cierre_aprobo_id')
    @api.depends_context('uid')
    def _compute_accion_pendiente_usuario(self):
        uid = self.env.uid
        for rec in self:
            acciones = []
            if rec.reviso_id.id == uid and not rec.firma_reviso_id:
                acciones.append(_('Firmar la revisión (sección 2)'))
            for act in rec.actividades_ids:
                if act.responsable_id.id == uid and not act.firma_enterado_id:
                    acciones.append(_('Firmar de enterado en tu actividad: "%s"') % (act.actividad or 'sin nombre'))
                    break
            for act in rec.actividades_ids:
                if act.verifico_id.id == uid and not act.firma_verifico_id:
                    acciones.append(_('Verificar la actividad: "%s"') % (act.actividad or 'sin nombre'))
                    break
            if rec.cierre_realizo_id.id == uid and not rec.firma_cierre_realizo_id:
                acciones.append(_('Firmar cierre — como "Realizó el control de cambios"'))
            if rec.cierre_reviso_id.id == uid and not rec.firma_cierre_reviso_id:
                acciones.append(_('Firmar cierre — como "Revisó la aplicación"'))
            if rec.cierre_aprobo_id.id == uid and not rec.firma_cierre_aprobo_id:
                acciones.append(_('Firmar cierre — como "Aprobó la aplicación del cambio"'))
            rec.accion_pendiente_usuario = ' / '.join(acciones) if acciones else ''

    # ── Secuencia ────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = (self.env['ir.sequence']
                                .next_by_code('amunet.solicitud.cambio') or 'Nuevo')
        return super().create(vals_list)

    def write(self, vals):
        campos_cierre = {
            'cierre_realizo_id': _('Realizó el control de cambios'),
            'cierre_reviso_id':  _('Revisó la aplicación'),
            'cierre_aprobo_id':  _('Aprobó la aplicación del cambio'),
        }
        old = {r.id: {f: r[f].id for f in campos_cierre} for r in self}
        result = super().write(vals)
        for campo, etiqueta in campos_cierre.items():
            if campo in vals:
                for r in self:
                    nuevo_id = r[campo].id
                    if nuevo_id and nuevo_id != old[r.id].get(campo):
                        r._notificar_firmante_cierre(r[campo], etiqueta)
        return result

    def _verificar_implementacion_completa(self):
        self.ensure_one()
        if self.implementacion_notificada or self.state != 'aceptado':
            return
        actividades = self.actividades_ids
        if not actividades:
            return
        sin_enterado = actividades.filtered(lambda a: a.responsable_id and not a.firma_enterado_id)
        sin_verificar = actividades.filtered(lambda a: a.verifico_id and not a.firma_verifico_id)
        if sin_enterado or sin_verificar:
            return
        grupo = self.env.ref('amunet_cc_general.group_cc_general_manager')
        managers = grupo.user_ids
        if not managers:
            return
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = '%s/odoo/control-de-cambios/%s' % (base_url, self.id)
        self.message_post(
            body=_(
                'Todas las actividades del control de cambios <b>%s</b> han sido firmadas de enterado y verificadas.<br/>'
                'Ya puedes documentar los resultados de la verificación y gestionar el cierre: '
                '<a href="%s">%s</a>'
            ) % (self.name, url, url),
            partner_ids=managers.mapped('partner_id').ids,
            subtype_xmlid='mail.mt_comment',
        )
        self.implementacion_notificada = True

    def _verificar_cierre_completo(self):
        self.ensure_one()
        if self.cierre_notificado or self.state != 'aceptado':
            return
        if not (self.firma_cierre_realizo_id and self.firma_cierre_reviso_id and self.firma_cierre_aprobo_id):
            return
        grupo = self.env.ref('amunet_cc_general.group_cc_general_manager')
        managers = grupo.user_ids
        if not managers:
            return
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = '%s/odoo/control-de-cambios/%s' % (base_url, self.id)
        self.message_post(
            body=_(
                'Las tres firmas de cierre del control de cambios <b>%s</b> están completas.<br/>'
                'Ya puedes cerrarlo: <a href="%s">%s</a>'
            ) % (self.name, url, url),
            partner_ids=managers.mapped('partner_id').ids,
            subtype_xmlid='mail.mt_comment',
        )
        self.cierre_notificado = True

    def _notificar_firmante_cierre(self, usuario, rol):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = '%s/odoo/control-de-cambios/%s' % (base_url, self.id)
        self.message_post(
            body=_(
                'Hola <b>%s</b>,<br/><br/>'
                'Se te asignó como <b>"%s"</b> en el cierre del control de cambios <b>%s</b>.<br/><br/>'
                'Cuando estés listo/a, abre el control de cambios, ve a la sección '
                '"Firmas de cierre" y haz clic en el botón <b>"Firmar"</b> de tu bloque.<br/><br/>'
                '<a href="%s">Abrir control de cambios %s</a>'
            ) % (usuario.name, rol, self.name, url, self.name),
            partner_ids=[usuario.partner_id.id],
            subtype_xmlid='mail.mt_comment',
        )

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
            if r.reviso_id:
                r.message_post(
                    body=_(
                        'Hola <b>%s</b>,<br/><br/>'
                        'El control de cambios <b>%s</b> requiere tu revisión.<br/><br/>'
                        'Abre el control de cambios y haz clic en el botón <b>"Firmar"</b> '
                        'de la sección "Revisó (Aseguramiento de Calidad)".<br/><br/>'
                        '<a href="%s">Abrir control de cambios %s</a>'
                    ) % (r.reviso_id.name, r.name, url, r.name),
                    partner_ids=[r.reviso_id.partner_id.id],
                    subtype_xmlid='mail.mt_comment',
                )
            r.message_post(
                body=_(
                    'Hola <b>%s</b>,<br/><br/>'
                    'El control de cambios <b>%s</b> requiere tu autorización.<br/><br/>'
                    'Abre el control de cambios y haz clic en el botón <b>"Autorizar"</b> '
                    '(disponible cuando la revisión de calidad esté firmada).<br/><br/>'
                    '<a href="%s">Abrir control de cambios %s</a>'
                ) % (r.aprobo_id.name, r.name, url, r.name),
                partner_ids=[r.aprobo_id.partner_id.id],
                subtype_xmlid='mail.mt_comment',
            )

    def action_aceptar(self):
        self.ensure_one()
        if self.state != 'pendiente':
            raise UserError(_('Solo puedes autorizar registros en revisión.'))
        if self.reviso_id and not self.firma_reviso_id:
            raise UserError(_(
                'No se puede autorizar: %s aún no ha firmado la revisión.'
            ) % self.reviso_id.name)
        return self._abrir_firma('_signature_aprobo', _('Autorización del cambio'))

    def _signature_aprobo(self):
        self.ensure_one()
        self.write({'state': 'aceptado',
                    'firma_aprobo_id': self.env.user.id,
                    'fecha_aprobo': fields.Datetime.now(),
                    'vb_aprobo': 'si'})
        self._message_log(body=_('<p><b>%s</b> autorizó el control de cambios.</p>') % self.env.user.name)
        if self.solicitante_id and self.solicitante_id.partner_id:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = '%s/odoo/control-de-cambios/%s' % (base_url, self.id)
            self.message_post(
                body=_(
                    'Hola <b>%s</b>,<br/><br/>'
                    'Tu control de cambios <b>%s</b> ha sido <b>autorizado</b> por %s.<br/><br/>'
                    'Ya puedes ingresar el plan de implementación: abre el control de cambios, '
                    've a la sección "Implementación y seguimiento" y agrega las actividades '
                    'con sus responsables.<br/><br/>'
                    '<a href="%s">Abrir control de cambios %s</a>'
                ) % (self.solicitante_id.name, self.name, self.env.user.name, url, self.name),
                partner_ids=self.solicitante_id.partner_id.ids,
                subtype_xmlid='mail.mt_comment',
            )

    def action_rechazar(self):
        self.ensure_one()
        if self.state != 'pendiente':
            raise UserError(_('Solo puedes rechazar registros en revisión.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rechazar control de cambios'),
            'res_model': 'amunet.cc.rechazo.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_cc_id': self.id},
        }

    def action_cerrar(self):
        for r in self:
            if r.state != 'aceptado':
                raise UserError(_('Solo puedes cerrar un registro autorizado.'))
            sin_enterado = r.actividades_ids.filtered(
                lambda a: a.responsable_id and not a.firma_enterado_id)
            if sin_enterado:
                nombres = ', '.join(sin_enterado.mapped('responsable_id.name'))
                raise UserError(_(
                    'No se puede cerrar: las siguientes personas aún no han firmado de enterado: %s'
                ) % nombres)
            sin_verificar = r.actividades_ids.filtered(
                lambda a: a.verifico_id and not a.firma_verifico_id)
            if sin_verificar:
                actividades = ', '.join(sin_verificar.mapped('actividad') or ['(sin nombre)'])
                raise UserError(_(
                    'No se puede cerrar: las siguientes actividades aún no han sido verificadas: %s'
                ) % actividades)
            r.state = 'cerrado'

    # ── Firmas con PIN ───────────────────────────────────────────
    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_solicitante':    _('Firma del solicitante'),
            '_signature_reviso':         _('Firma de quien revisó'),
            '_signature_aprobo':         _('Autorización del cambio'),
            '_signature_cierre':         _('Firma de cierre'),
            '_signature_cierre_realizo': _('Realizó el control de cambios'),
            '_signature_cierre_reviso':  _('Revisó la aplicación'),
            '_signature_cierre_aprobo':  _('Aprobó la aplicación del cambio'),
        }

    def _abrir_firma(self, method_name, label):
        self.ensure_one()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, method_name, label,
            _('Control de cambios: %s') % (self.name or ''))

    def action_firmar_solicitante(self):
        self.ensure_one()
        if self.firma_solicitante_id:
            raise UserError(_('Ya se registró la firma del solicitante.'))
        if self.solicitante_id and self.solicitante_id != self.env.user:
            raise UserError(_('Solo %s puede firmar como solicitante.') % self.solicitante_id.name)
        return self._abrir_firma('_signature_solicitante', _('Firma del solicitante'))

    def _signature_solicitante(self):
        self.ensure_one()
        self.write({'firma_solicitante_id': self.env.user.id,
                    'fecha_solicitante': fields.Datetime.now()})
        self._message_log(body=_('<p><b>%s</b> firmó como Solicitante.</p>') % self.env.user.name)

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

    def action_firmar_cierre_realizo(self):
        self.ensure_one()
        if self.firma_cierre_realizo_id:
            raise UserError(_('Ya se registró esta firma.'))
        if self.cierre_realizo_id and self.cierre_realizo_id != self.env.user:
            raise UserError(_('Solo %s puede firmar en este espacio.') % self.cierre_realizo_id.name)
        return self._abrir_firma('_signature_cierre_realizo', _('Realizó el control de cambios'))

    def _signature_cierre_realizo(self):
        self.ensure_one()
        self.write({'firma_cierre_realizo_id': self.env.user.id,
                    'fecha_cierre_realizo': fields.Datetime.now()})
        self._message_log(body=_('<p><b>%s</b> firmó como Realizó el control de cambios.</p>') % self.env.user.name)
        self._verificar_cierre_completo()

    def action_firmar_cierre_reviso(self):
        self.ensure_one()
        if self.firma_cierre_reviso_id:
            raise UserError(_('Ya se registró esta firma.'))
        if self.cierre_reviso_id and self.cierre_reviso_id != self.env.user:
            raise UserError(_('Solo %s puede firmar en este espacio.') % self.cierre_reviso_id.name)
        return self._abrir_firma('_signature_cierre_reviso', _('Revisó la aplicación'))

    def _signature_cierre_reviso(self):
        self.ensure_one()
        self.write({'firma_cierre_reviso_id': self.env.user.id,
                    'fecha_cierre_reviso': fields.Datetime.now()})
        self._message_log(body=_('<p><b>%s</b> firmó como Revisó la aplicación.</p>') % self.env.user.name)
        self._verificar_cierre_completo()

    def action_firmar_cierre_aprobo(self):
        self.ensure_one()
        if self.firma_cierre_aprobo_id:
            raise UserError(_('Ya se registró esta firma.'))
        if self.cierre_aprobo_id and self.cierre_aprobo_id != self.env.user:
            raise UserError(_('Solo %s puede firmar en este espacio.') % self.cierre_aprobo_id.name)
        return self._abrir_firma('_signature_cierre_aprobo', _('Aprobó la aplicación del cambio'))

    def _signature_cierre_aprobo(self):
        self.ensure_one()
        self.write({'firma_cierre_aprobo_id': self.env.user.id,
                    'fecha_cierre_aprobo': fields.Datetime.now()})
        self._message_log(body=_('<p><b>%s</b> firmó como Aprobó la aplicación del cambio.</p>') % self.env.user.name)
        self._verificar_cierre_completo()

    def action_descartar(self):
        for r in self:
            if r.state != 'borrador':
                raise UserError(_('Solo puedes eliminar un registro en borrador.'))
        self.unlink()
        return {'type': 'ir.actions.client', 'tag': 'history_back'}
