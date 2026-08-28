from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AmunetArea(models.Model):
    _name = 'amunet.desviacion.area'
    _description = 'Área de Amunet (catálogo para desviaciones)'
    _order = 'name'

    name = fields.Char(string='Área', required=True)


class AmunetDesviacionAccion(models.Model):
    _name = 'amunet.desviacion.accion'
    _description = 'Acción correctiva / preventiva de desviación'
    _order = 'tipo, id'

    desviacion_id  = fields.Many2one('amunet.desviacion', required=True, ondelete='cascade')
    tipo           = fields.Selection([
        ('correctiva', 'Correctiva'),
        ('preventiva', 'Preventiva'),
    ], string='Tipo', required=True, default='correctiva')
    descripcion    = fields.Text(string='Descripción de la acción', required=True)
    responsable_id = fields.Many2one('res.users', string='Responsable')
    fecha_limite   = fields.Date(string='Fecha límite')
    state          = fields.Selection([
        ('pendiente',  'Pendiente'),
        ('realizada',  'Realizada'),
        ('verificada', 'Verificada'),
    ], string='Estado', default='pendiente', required=True)
    fecha_cierre        = fields.Date(string='Fecha de cierre')
    evidencia_cierre    = fields.Text(string='Evidencia del cumplimiento')

    def _notificar_responsable(self):
        for accion in self.filtered(lambda a: a.responsable_id and a.desviacion_id):
            desviacion = accion.desviacion_id
            responsable = accion.responsable_id
            tipo_label = dict(accion._fields['tipo'].selection).get(accion.tipo, accion.tipo)
            desviacion.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Acción %s asignada — %s') % (tipo_label, desviacion.name),
                note=_(
                    '<p>Se te asignó una acción <b>%s</b> en la desviación <b>%s</b>.</p>'
                    '<p><b>Acción:</b> %s</p>'
                    '<p><b>Fecha límite:</b> %s</p>'
                    '<p>Ingresa a la desviación, completa la acción y actualiza su estado a <b>Realizada</b>.</p>'
                ) % (
                    tipo_label,
                    desviacion.name,
                    accion.descripcion or '',
                    accion.fecha_limite or _('No definida'),
                ),
                user_id=responsable.id,
                date_deadline=accion.fecha_limite,
            )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._notificar_responsable()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'responsable_id' in vals:
            self._notificar_responsable()
        return res

    def action_marcar_realizada(self):
        for accion in self:
            if accion.responsable_id and accion.responsable_id != self.env.user:
                raise UserError(_(
                    'Solo %s puede marcar esta acción como Realizada.'
                ) % accion.responsable_id.name)
            accion.write({
                'state': 'realizada',
                'fecha_cierre': fields.Date.today(),
            })
            accion.desviacion_id._message_log(
                body=_('<p><b>%s</b> marcó como <b>Realizada</b> la acción: %s</p>') % (
                    self.env.user.name, accion.descripcion or ''))

    def action_verificar(self):
        puede = (
            self.env.user.has_group('amunet_documentos.group_responsable_sanitario') or
            self.env.user.has_group('amunet_desviaciones.group_desviaciones_manager')
        )
        if not puede:
            raise UserError(_(
                'Solo el Responsable Sanitario o el Responsable de Desviaciones puede verificar acciones.'))
        for accion in self:
            if accion.state != 'realizada':
                raise UserError(_('Solo puedes verificar una acción que ya fue marcada como Realizada.'))
            accion.write({'state': 'verificada'})
            accion.desviacion_id._message_log(
                body=_('<p><b>%s</b> verificó la acción: %s</p>') % (
                    self.env.user.name, accion.descripcion or ''))


class AmunetDesviacion(models.Model):
    _name = 'amunet.desviacion'
    _description = 'Desviación / No Conformidad'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    # ── Folio ─────────────────────────────────────────────────────────
    name = fields.Char(string='Folio', readonly=True, copy=False, default='Nuevo')

    state = fields.Selection([
        ('borrador',      'Borrador'),
        ('investigacion', 'En investigación'),
        ('cerrado',       'Cerrado'),
        ('no_procede',    'No procede'),
    ], string='Estado', default='borrador', required=True, tracking=True)

    # ── Sección 1: Identificación ──────────────────────────────────────
    fecha_reporte  = fields.Date(string='Fecha de reporte', default=fields.Date.today, required=True)
    clasif_interna = fields.Boolean(string='Interna')
    clasif_externa = fields.Boolean(string='Externa (auditoría, queja)')
    tipo_incidencia = fields.Selection([
        ('producto', 'Producto'),
        ('proceso',  'Proceso'),
    ], string='Tipo de incidencia', required=True, default='proceso', tracking=True)
    producto       = fields.Char(string='Producto / Proceso')
    lote           = fields.Char(string='No. Lote')
    area_afectada  = fields.Char(string='Área afectada')
    reporta_id     = fields.Many2one('res.users', string='Quien reporta', default=lambda self: self.env.user)
    descripcion    = fields.Text(string='Descripción de la desviación / NC')
    evidencia      = fields.Text(string='Descripción de la evidencia objetiva')
    evidencia_adjunta_ids = fields.Many2many(
        'ir.attachment', 'amunet_desviacion_adjunto_rel', 'desviacion_id', 'attachment_id',
        string='Evidencia objetiva adjunta',
    )

    # ── Producto: campos condicionales al lote ────────────────────────
    producto_salio_mercado = fields.Selection([
        ('si',  'Sí — ya fue distribuido'),
        ('no',  'No — aún en planta'),
        ('parcial', 'Parcial — parte del lote fue distribuido'),
    ], string='¿El producto ya salió al mercado?')
    disposicion_producto = fields.Selection([
        ('cuarentena',  'Cuarentena'),
        ('rechazo',     'Rechazo / destrucción'),
        ('reproceso',   'Reproceso'),
        ('concesion',   'Liberación bajo concesión'),
    ], string='Disposición del producto no conforme')
    requiere_cofepris = fields.Boolean(string='¿Requiere notificación a Cofepris?')
    referencia_cofepris = fields.Char(string='Referencia del reporte Cofepris')

    # ── Proceso: campos condicionales cuando no hay lote ─────────────
    proceso_suspendido    = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
    ], string='¿Se suspendió el proceso mientras se investiga?')
    procedimiento_afectado = fields.Char(string='Procedimiento / instrucción afectada',
                                         placeholder='Ej. PNO-LAB-012, Instrucción de trabajo IT-005')
    afecta_otras_areas    = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
    ], string='¿Afecta a otras áreas?')
    areas_impactadas_ids  = fields.Many2many(
        'amunet.desviacion.area',
        'amunet_desviacion_area_rel',
        'desviacion_id', 'area_id',
        string='Áreas impactadas')

    # ── Sección 2: Investigación y valoración ─────────────────────────
    criterio              = fields.Text(string='Criterio de referencia (procedimiento, norma, especificación)')
    valoracion            = fields.Selection([
        ('procede',    'Procede (es una desviación real)'),
        ('no_procede', 'No procede (se descarta)'),
    ], string='Valoración de la desviación')
    resolucion_no_procede = fields.Text(string='Motivo (si no procede)')

    # ── Sección 3: Análisis de causa raíz ────────────────────────────
    herramienta_ishikawa = fields.Boolean(string='Diagrama de Ishikawa')
    herramienta_5porque  = fields.Boolean(string='5 Porqués')
    # 5 Porqués
    porque_1 = fields.Text(string='1. ¿Por qué ocurrió?')
    porque_2 = fields.Text(string='2. ¿Por qué? (causa de la anterior)')
    porque_3 = fields.Text(string='3. ¿Por qué? (causa de la anterior)')
    porque_4 = fields.Text(string='4. ¿Por qué? (causa de la anterior)')
    porque_5 = fields.Text(string='5. ¿Por qué? — Causa raíz')

    # Ishikawa (6M)
    ishikawa_mano_obra      = fields.Text(string='Mano de obra')
    ishikawa_maquina        = fields.Text(string='Máquina / Equipo')
    ishikawa_metodo         = fields.Text(string='Método')
    ishikawa_material       = fields.Text(string='Material / Insumo')
    ishikawa_medicion       = fields.Text(string='Medición')
    ishikawa_medio_ambiente = fields.Text(string='Medio ambiente')

    causas = fields.Text(string='Causa(s) identificada(s) / Descripción del análisis')

    severidad    = fields.Selection([
        ('baja',    'Baja (afecta documentación o estética)'),
        ('media',   'Media (afecta calidad pero no seguridad)'),
        ('alta',    'Alta (afecta seguridad o eficacia de prueba)'),
        ('critica', 'Crítica (riesgo para la salud del consumidor)'),
    ], string='Severidad (impacto)')
    probabilidad = fields.Selection([
        ('baja',  'Baja (caso aislado)'),
        ('media', 'Media (puede volver a ocurrir)'),
        ('alta',  'Alta (es sistémico)'),
    ], string='Probabilidad de recurrencia')
    nivel_riesgo        = fields.Char(string='Nivel de riesgo', compute='_compute_nivel_riesgo', store=True)
    clasificacion_final = fields.Selection([
        ('critica', 'Crítica'),
        ('mayor',   'Mayor'),
        ('menor',   'Menor'),
    ], string='Clasificación final', compute='_compute_clasificacion_final', store=True)

    # ── Sección 4: Conclusión ─────────────────────────────────────────
    conclusion  = fields.Text(string='Conclusión del análisis')
    lecciones   = fields.Text(string='Lecciones aprendidas')
    deriva_cc   = fields.Selection([('si', 'Sí'), ('no', 'No')], string='¿Deriva en un Control de Cambios?')
    folio_cc_id = fields.Many2one('amunet.cc.general', string='Control de Cambios relacionado',
                                  domain="[('state', 'not in', ['borrador', 'rechazado'])]")

    # ── Sección 5: Firmas ─────────────────────────────────────────────
    emisor_id               = fields.Many2one('res.users', string='Emisor (quien reporta)')
    firma_emisor_id         = fields.Many2one('res.users', string='Firma emisor', readonly=True)
    fecha_firma_emisor      = fields.Datetime(string='Fecha firma emisor', readonly=True)

    supervisor_id           = fields.Many2one('res.users', string='Supervisor de área')
    firma_supervisor_id     = fields.Many2one('res.users', string='Firma supervisor', readonly=True)
    fecha_firma_supervisor  = fields.Datetime(string='Fecha firma supervisor', readonly=True)

    responsable_id          = fields.Many2one('res.users', string='Responsable (análisis y conclusión)')
    firma_responsable_id    = fields.Many2one('res.users', string='Firma responsable', readonly=True)
    fecha_firma_responsable = fields.Datetime(string='Fecha firma responsable', readonly=True)

    verifico_id             = fields.Many2one('res.users', string='Verificó (Calidad / Gerencia)')
    firma_verifico_id       = fields.Many2one('res.users', string='Firma verificó', readonly=True)
    fecha_firma_verifico    = fields.Datetime(string='Fecha firma verificó', readonly=True)

    # ── Plan de acciones correctivas / preventivas ────────────────────
    accion_ids = fields.One2many(
        'amunet.desviacion.accion', 'desviacion_id',
        string='Plan de acciones')
    adjunto_acciones_ids = fields.Many2many(
        'ir.attachment',
        'amunet_desviacion_evidencia_adjunto_rel',
        'desviacion_id', 'attachment_id',
        string='Anexos de evidencia del plan de acciones')

    # ── Cierre ────────────────────────────────────────────────────────
    fecha_cierre       = fields.Date(string='Fecha de cierre')
    conclusion_cierre  = fields.Text(string='Conclusión de cierre')
    cerro_id           = fields.Many2one('res.users', string='Cerró', readonly=True)
    firma_cerro_id     = fields.Many2one('res.users', string='Firma cierre', readonly=True)
    fecha_firma_cierre = fields.Datetime(string='Fecha firma cierre', readonly=True)

    # ── Computed ──────────────────────────────────────────────────────
    is_manager = fields.Boolean(compute='_compute_is_manager', compute_sudo=False)

    @api.depends_context('uid')
    def _compute_is_manager(self):
        is_mgr = self.env.user.has_group('amunet_desviaciones.group_desviaciones_manager')
        for rec in self:
            rec.is_manager = is_mgr

    @api.depends('nivel_riesgo')
    def _compute_clasificacion_final(self):
        for rec in self:
            if rec.nivel_riesgo.startswith('CRÍTICO'):
                rec.clasificacion_final = 'critica'
            elif rec.nivel_riesgo.startswith('ALTO'):
                rec.clasificacion_final = 'mayor'
            elif rec.nivel_riesgo:
                rec.clasificacion_final = 'menor'
            else:
                rec.clasificacion_final = False

    @api.depends('severidad', 'probabilidad')
    def _compute_nivel_riesgo(self):
        matriz = {
            ('critica', 'alta'):  'CRÍTICO — Acción inmediata',
            ('critica', 'media'): 'CRÍTICO — Acción inmediata',
            ('critica', 'baja'):  'ALTO — Requiere CAPA urgente',
            ('alta',    'alta'):  'CRÍTICO — Acción inmediata',
            ('alta',    'media'): 'ALTO — Requiere CAPA urgente',
            ('alta',    'baja'):  'ALTO — Requiere CAPA urgente',
            ('media',   'alta'):  'ALTO — Requiere CAPA urgente',
            ('media',   'media'): 'MEDIO — Requiere seguimiento',
            ('media',   'baja'):  'MEDIO — Requiere seguimiento',
            ('baja',    'alta'):  'MEDIO — Requiere seguimiento',
            ('baja',    'media'): 'BAJO — Monitorear',
            ('baja',    'baja'):  'BAJO — Monitorear',
        }
        for rec in self:
            rec.nivel_riesgo = matriz.get((rec.severidad, rec.probabilidad), '')

    # ── Folio automático ──────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == 'Nuevo':
                today = fields.Date.today()
                mm = '%02d' % today.month
                yy = '%02d' % (today.year % 100)
                seq = self.env['ir.sequence'].next_by_code('amunet.desviacion') or '001'
                vals['name'] = 'DV-%s%s-%s' % (mm, yy, seq)
        return super().create(vals_list)

    # ── Acciones de estado ────────────────────────────────────────────
    def action_iniciar_investigacion(self):
        for rec in self:
            if rec.state != 'borrador':
                raise UserError(_('Solo puedes iniciar investigación desde borrador.'))
            faltantes = []
            if not rec.clasif_interna and not rec.clasif_externa:
                faltantes.append('• Clasificación (interna o externa)')
            if not rec.descripcion:
                faltantes.append('• Descripción de la desviación')
            if not rec.reporta_id:
                faltantes.append('• Quién reporta')
            if faltantes:
                raise UserError(_('Completa los siguientes campos antes de iniciar:\n\n%s') % '\n'.join(faltantes))
            rec.state = 'investigacion'

    def action_cerrar(self):
        puede_cerrar = (
            self.env.user.has_group('amunet_documentos.group_responsable_sanitario') or
            self.env.user.has_group('amunet_desviaciones.group_desviaciones_manager')
        )
        if not puede_cerrar:
            raise UserError(_('Solo el Responsable Sanitario o el Responsable de Desviaciones puede cerrar una desviación.'))
        for rec in self:
            if rec.state != 'investigacion':
                raise UserError(_('Solo puedes cerrar desde "En investigación".'))
            if not rec.conclusion_cierre:
                raise UserError(_('Escribe la conclusión de cierre antes de cerrar.'))
            pendientes = rec.accion_ids.filtered(lambda a: a.state == 'pendiente')
            if pendientes:
                descripciones = '\n'.join('• ' + (a.descripcion or '(sin descripción)') for a in pendientes)
                raise UserError(_(
                    'No puedes cerrar la desviación mientras haya acciones pendientes:\n\n%s\n\n'
                    'Marca cada acción como Realizada o Verificada antes de cerrar.'
                ) % descripciones)
            rec.write({
                'state':      'cerrado',
                'cerro_id':   self.env.uid,
                'fecha_cierre': fields.Date.today(),
            })

    def action_no_procede(self):
        for rec in self:
            if rec.state != 'investigacion':
                raise UserError(_('Solo puedes marcar "No procede" desde "En investigación".'))
            if not rec.resolucion_no_procede:
                raise UserError(_('Explica el motivo por el que no procede.'))
            rec.state = 'no_procede'

    def action_reabrir(self):
        raise UserError(_('Una desviación cerrada no puede reabrirse. Si el problema volvió a ocurrir, abre una nueva desviación.'))

    # ── Firmas con wizard genérico ────────────────────────────────────
    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_emisor':      _('Firma del emisor'),
            '_signature_supervisor':  _('Firma del supervisor de área'),
            '_signature_responsable': _('Firma del responsable'),
            '_signature_verifico':    _('Firma de quien verificó'),
            '_signature_cierre':      _('Firma de cierre'),
        }

    def _abrir_firma(self, method_name, label):
        self.ensure_one()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, method_name, label, _('Desviación: %s') % (self.name or ''))

    def action_firmar_emisor(self):
        self.ensure_one()
        if self.firma_emisor_id:
            raise UserError(_('Ya se registró esta firma.'))
        if self.emisor_id and self.emisor_id != self.env.user:
            raise UserError(_('Solo %s puede firmar en este espacio.') % self.emisor_id.name)
        return self._abrir_firma('_signature_emisor', _('Firma del emisor'))

    def _signature_emisor(self):
        self.ensure_one()
        self.write({'firma_emisor_id': self.env.user.id, 'fecha_firma_emisor': fields.Datetime.now()})
        self._message_log(body=_('<p><b>%s</b> firmó como Emisor.</p>') % self.env.user.name)

    def action_firmar_supervisor(self):
        self.ensure_one()
        if self.firma_supervisor_id:
            raise UserError(_('Ya se registró esta firma.'))
        if self.supervisor_id and self.supervisor_id != self.env.user:
            raise UserError(_('Solo %s puede firmar en este espacio.') % self.supervisor_id.name)
        return self._abrir_firma('_signature_supervisor', _('Firma del supervisor'))

    def _signature_supervisor(self):
        self.ensure_one()
        self.write({'firma_supervisor_id': self.env.user.id, 'fecha_firma_supervisor': fields.Datetime.now()})
        self._message_log(body=_('<p><b>%s</b> firmó como Supervisor de área.</p>') % self.env.user.name)

    def action_firmar_responsable(self):
        self.ensure_one()
        if self.firma_responsable_id:
            raise UserError(_('Ya se registró esta firma.'))
        if self.responsable_id and self.responsable_id != self.env.user:
            raise UserError(_('Solo %s puede firmar en este espacio.') % self.responsable_id.name)
        pendientes = self.accion_ids.filtered(lambda a: a.state == 'pendiente')
        if pendientes:
            descripciones = '\n'.join('• ' + (a.descripcion or '(sin descripción)') for a in pendientes)
            raise UserError(_(
                'No puedes firmar como Responsable mientras haya acciones pendientes de realizar:\n\n%s'
            ) % descripciones)
        return self._abrir_firma('_signature_responsable', _('Firma del responsable'))

    def _signature_responsable(self):
        self.ensure_one()
        self.write({'firma_responsable_id': self.env.user.id, 'fecha_firma_responsable': fields.Datetime.now()})
        self._message_log(body=_('<p><b>%s</b> firmó como Responsable.</p>') % self.env.user.name)

    def action_firmar_verifico(self):
        self.ensure_one()
        if self.firma_verifico_id:
            raise UserError(_('Ya se registró esta firma.'))
        if self.verifico_id and self.verifico_id != self.env.user:
            raise UserError(_('Solo %s puede firmar en este espacio.') % self.verifico_id.name)
        pendientes = self.accion_ids.filtered(lambda a: a.state == 'pendiente')
        if pendientes:
            descripciones = '\n'.join('• ' + (a.descripcion or '(sin descripción)') for a in pendientes)
            raise UserError(_(
                'No puedes firmar como Verificó mientras haya acciones pendientes de realizar:\n\n%s'
            ) % descripciones)
        return self._abrir_firma('_signature_verifico', _('Firma de quien verificó'))

    def _signature_verifico(self):
        self.ensure_one()
        self.write({'firma_verifico_id': self.env.user.id, 'fecha_firma_verifico': fields.Datetime.now()})
        self._message_log(body=_('<p><b>%s</b> firmó como Verificó.</p>') % self.env.user.name)

    def action_firmar_cierre(self):
        self.ensure_one()
        if self.firma_cerro_id:
            raise UserError(_('Ya se registró la firma de cierre.'))
        return self._abrir_firma('_signature_cierre', _('Firma de cierre'))

    def _signature_cierre(self):
        self.ensure_one()
        self.write({'firma_cerro_id': self.env.user.id, 'fecha_firma_cierre': fields.Datetime.now()})
        self._message_log(body=_('<p><b>%s</b> firmó el cierre.</p>') % self.env.user.name)
