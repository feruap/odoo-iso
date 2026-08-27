from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_TIPO = [
    ('inicial',       'Inicial'),
    ('seguimiento',   'Seguimiento'),
    ('extraordinaria','Extraordinaria'),
]


class AmunetAperturaCierreProv(models.Model):
    _name = 'amunet.apertura.cierre.prov'
    _description = 'Registro de Apertura y Cierre de Auditoría de Proveedores (F-DC-005-017)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_auditoria_inicio desc, id desc'
    _rec_name = 'clave'

    clave = fields.Char(string='No. Registro', readonly=True, copy=False,
                        default=lambda self: _('Nuevo'))
    plan_id         = fields.Many2one('amunet.plan.audit.prov', string='Plan de auditoría relacionado',
                                      ondelete='set null')
    proveedor       = fields.Char(string='Nombre del proveedor', required=True)
    fecha_auditoria_inicio = fields.Date(string='Fecha inicio de auditoría', required=True)
    fecha_auditoria_fin    = fields.Date(string='Fecha fin de auditoría')
    tipo            = fields.Selection(_TIPO, string='Tipo de auditoría', required=True, default='inicial')
    lider_id        = fields.Many2one('res.users', string='Auditor Líder', required=True)
    auditor_ids     = fields.Many2many('res.users', 'apertura_cierre_auditor_rel',
                                       'registro_id', 'user_id', string='Auditores internos')
    acompanante     = fields.Char(string='Acompañante del proveedor (nombre y cargo)')
    state           = fields.Selection([
        ('borrador', 'Borrador'),
        ('vigente',  'Vigente'),
        ('cerrado',  'Cerrado'),
    ], default='borrador', string='Estado', required=True, tracking=True)

    # ── 2. Reunión de apertura ───────────────────────────────────────────────
    ap_fecha        = fields.Date(string='Fecha de apertura')
    ap_hora_inicio  = fields.Char(string='Hora inicio', placeholder='09:00')
    ap_hora_fin     = fields.Char(string='Hora fin',    placeholder='09:30')
    ap_lugar        = fields.Char(string='Lugar')

    ap_asistente_ids  = fields.One2many('amunet.ap.prov.asistente',  'registro_id', string='Asistentes (apertura)')
    ap_compromiso_ids = fields.One2many('amunet.ap.prov.compromiso', 'registro_id', string='Compromisos (apertura)')

    # Agenda apertura
    ap_presentacion_equipo   = fields.Boolean('Presentación del equipo auditor')
    ap_confirm_objetivo      = fields.Boolean('Confirmación del objetivo de la auditoría')
    ap_confirm_alcance       = fields.Boolean('Confirmación del alcance de la auditoría')
    ap_confirm_criterios     = fields.Boolean('Confirmación de los criterios de auditoría')
    ap_cronograma            = fields.Boolean('Presentación del programa / cronograma')
    ap_disponibilidad        = fields.Boolean('Confirmación de disponibilidad (personal, instalaciones, documentos)')
    ap_canales_comunicacion  = fields.Boolean('Acuerdo sobre canales de comunicación')
    ap_acuerdo_cierre        = fields.Boolean('Acuerdo sobre fecha, hora y lugar de la reunión de cierre')
    ap_acuerdo_cierre_detalle= fields.Char(string='Detalle acuerdo reunión de cierre')
    ap_otros                 = fields.Boolean('Otros')
    ap_otros_texto           = fields.Char(string='Otros (especificar)')
    ap_observaciones         = fields.Text(string='Observaciones / comentarios del proveedor (apertura)')

    # ── 3. Reunión de cierre ─────────────────────────────────────────────────
    ci_fecha        = fields.Date(string='Fecha de cierre')
    ci_hora_inicio  = fields.Char(string='Hora inicio', placeholder='16:00')
    ci_hora_fin     = fields.Char(string='Hora fin',    placeholder='17:00')
    ci_lugar        = fields.Char(string='Lugar')

    ci_asistente_ids  = fields.One2many('amunet.ci.prov.asistente',  'registro_id', string='Asistentes (cierre)')
    ci_compromiso_ids = fields.One2many('amunet.ci.prov.compromiso', 'registro_id', string='Compromisos (cierre)')

    # Agenda cierre
    ci_agradecimiento        = fields.Boolean('Agradecimiento por la colaboración')
    ci_resumen_auditoria     = fields.Boolean('Presentación del resumen de la auditoría')
    ci_recordatorio_hallazgos= fields.Boolean('Recordatorio: hallazgos detallados constan en formato aparte')
    ci_plazo_informe         = fields.Boolean('Acuerdo de plazos para la entrega del informe final')
    ci_plazo_pac             = fields.Boolean('Acuerdo de plazos para la presentación del PAC')
    ci_fecha_seguimiento     = fields.Boolean('Acuerdo sobre fecha de seguimiento (si aplica)')
    ci_preguntas             = fields.Boolean('Turno de preguntas y aclaraciones')
    ci_otros                 = fields.Boolean('Otros')
    ci_otros_texto           = fields.Char(string='Otros (especificar)')

    # Resumen auditoría
    ci_areas_auditadas       = fields.Text(string='Áreas auditadas')
    ci_documentacion_revisada= fields.Text(string='Documentación revisada')
    ci_fortalezas            = fields.Text(string='Fortalezas observadas')
    ci_oportunidades         = fields.Text(string='Oportunidades de mejora identificadas')
    ci_nc_total              = fields.Char(string='No conformidades detectadas (número total)')

    # Plazos acordados en cierre
    plazo_informe_preliminar = fields.Integer(string='Informe preliminar (días hábiles)', default=5)
    plazo_revision_prov      = fields.Integer(string='Revisión del informe por el proveedor (días hábiles)', default=10)
    plazo_informe_final      = fields.Integer(string='Informe final (días hábiles)', default=15)
    plazo_pac                = fields.Integer(string='Plan de Acciones Correctivas (días hábiles)', default=30)
    plazo_verificacion       = fields.Char(string='Verificación de cierre de acciones (fecha / condición)')

    ci_observaciones         = fields.Text(string='Observaciones / comentarios del proveedor (cierre)')

    # ── 4. Aprobaciones / Firmas ─────────────────────────────────────────────
    elaboro_id          = fields.Many2one('res.users', string='Auditor Líder (firma)', readonly=True)
    fecha_elaboro       = fields.Date(string='Fecha firma líder', readonly=True)
    resp_calidad_prov   = fields.Char(string='Responsable de Calidad del proveedor')
    firma_compras_id    = fields.Many2one('res.users', string='Firmó — Resp. de Compras', readonly=True)
    fecha_firma_compras = fields.Date(string='Fecha firma compras', readonly=True)

    # ── 5. Distribución ──────────────────────────────────────────────────────
    dist_archivo  = fields.Boolean('Archivo de Auditorías de Proveedores', default=True)
    dist_calidad  = fields.Boolean('Responsable de Calidad (fabricante)',  default=True)
    dist_compras  = fields.Boolean('Responsable de Compras (fabricante)',  default=True)
    dist_proveedor= fields.Boolean('Proveedor auditado',                   default=True)
    dist_otros    = fields.Char('Otros destinatarios')

    # ── Secuencia ────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('clave', _('Nuevo')) == _('Nuevo'):
                vals['clave'] = self.env['ir.sequence'].next_by_code(
                    'amunet.apertura.cierre.prov') or _('Nuevo')
        return super().create(vals_list)

    # ── Firma electrónica ────────────────────────────────────────────────────
    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_lider':   _('Firma del Auditor Líder — Registro Apertura/Cierre'),
            '_signature_compras': _('Firma del Responsable de Compras — Registro Apertura/Cierre'),
        }

    def action_firmar_lider(self):
        self.ensure_one()
        if self.elaboro_id:
            raise ValidationError(_('El Auditor Líder ya firmó este registro.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_lider',
            _('Auditor Líder'),
            _('Firma de elaboración del registro %s.') % self.clave,
        )

    def _signature_lider(self):
        self.ensure_one()
        self.write({
            'elaboro_id':    self.env.user.id,
            'fecha_elaboro': fields.Date.today(),
            'state':         'vigente',
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_firmar_compras(self):
        self.ensure_one()
        if not self.elaboro_id:
            raise ValidationError(_('El Auditor Líder debe firmar primero.'))
        if self.firma_compras_id:
            raise ValidationError(_('Responsable de Compras ya firmó este registro.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_compras',
            _('Responsable de Compras'),
            _('Firma de aprobación del registro %s.') % self.clave,
        )

    def _signature_compras(self):
        self.ensure_one()
        self.write({
            'firma_compras_id':    self.env.user.id,
            'fecha_firma_compras': fields.Date.today(),
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_cerrar(self):
        self.write({'state': 'cerrado'})

    def action_borrador(self):
        self.write({
            'state':            'borrador',
            'elaboro_id':       False,
            'fecha_elaboro':    False,
            'firma_compras_id': False,
            'fecha_firma_compras': False,
        })

    def unlink(self):
        if not self.env.user.has_group('amunet_documentos.group_documentos_manager'):
            raise ValidationError(_('Solo el gestor de documentos puede eliminar este registro.'))
        return super().unlink()


class AmunetApProvAsistente(models.Model):
    _name = 'amunet.ap.prov.asistente'
    _description = 'Asistentes — Reunión de Apertura'
    _order = 'registro_id, no, id'

    registro_id  = fields.Many2one('amunet.apertura.cierre.prov', required=True, ondelete='cascade')
    no           = fields.Integer(string='No.')
    nombre       = fields.Char(string='Nombre y Apellidos')
    cargo_rol    = fields.Char(string='Cargo / Rol')
    empresa      = fields.Char(string='Empresa')


class AmunetCiProvAsistente(models.Model):
    _name = 'amunet.ci.prov.asistente'
    _description = 'Asistentes — Reunión de Cierre'
    _order = 'registro_id, no, id'

    registro_id  = fields.Many2one('amunet.apertura.cierre.prov', required=True, ondelete='cascade')
    no           = fields.Integer(string='No.')
    nombre       = fields.Char(string='Nombre y Apellidos')
    cargo_rol    = fields.Char(string='Cargo / Rol')
    empresa      = fields.Char(string='Empresa')


class AmunetApProvCompromiso(models.Model):
    _name = 'amunet.ap.prov.compromiso'
    _description = 'Compromisos — Reunión de Apertura'
    _order = 'registro_id, no, id'

    registro_id  = fields.Many2one('amunet.apertura.cierre.prov', required=True, ondelete='cascade')
    no           = fields.Integer(string='Nº')
    compromiso   = fields.Char(string='Compromiso', required=True)
    responsable  = fields.Char(string='Responsable')
    fecha_limite = fields.Date(string='Fecha límite')


class AmunetCiProvCompromiso(models.Model):
    _name = 'amunet.ci.prov.compromiso'
    _description = 'Compromisos — Reunión de Cierre'
    _order = 'registro_id, no, id'

    registro_id  = fields.Many2one('amunet.apertura.cierre.prov', required=True, ondelete='cascade')
    no           = fields.Integer(string='Nº')
    compromiso   = fields.Char(string='Compromiso', required=True)
    responsable  = fields.Char(string='Responsable')
    fecha_limite = fields.Date(string='Fecha límite')
