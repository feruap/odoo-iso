from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_HORAS = [
    ('06:00', '6:00 AM'), ('06:30', '6:30 AM'),
    ('07:00', '7:00 AM'), ('07:30', '7:30 AM'),
    ('08:00', '8:00 AM'), ('08:30', '8:30 AM'),
    ('09:00', '9:00 AM'), ('09:30', '9:30 AM'),
    ('10:00', '10:00 AM'), ('10:30', '10:30 AM'),
    ('11:00', '11:00 AM'), ('11:30', '11:30 AM'),
    ('12:00', '12:00 PM'), ('12:30', '12:30 PM'),
    ('13:00', '1:00 PM'), ('13:30', '1:30 PM'),
    ('14:00', '2:00 PM'), ('14:30', '2:30 PM'),
    ('15:00', '3:00 PM'), ('15:30', '3:30 PM'),
    ('16:00', '4:00 PM'), ('16:30', '4:30 PM'),
    ('17:00', '5:00 PM'), ('17:30', '5:30 PM'),
    ('18:00', '6:00 PM'), ('18:30', '6:30 PM'),
    ('19:00', '7:00 PM'), ('19:30', '7:30 PM'),
    ('20:00', '8:00 PM'), ('20:30', '8:30 PM'),
    ('21:00', '9:00 PM'),
]


class AmunetActaAuditoria(models.Model):
    _name = 'amunet.acta.auditoria'
    _description = 'Acta de Apertura y Cierre de Auditoría'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'clave'
    _order = 'apertura_fecha desc, id'

    clave = fields.Char(string='Clave', readonly=True, copy=False,
        default=lambda self: _('Nuevo'))
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('firmado', 'Firmado'),
    ], default='borrador', string='Estado', tracking=True)

    # ── Vinculación al plan ────────────────────────────────────────────────
    plan_id = fields.Many2one('amunet.plan.auditoria', string='Plan de auditoría',
        required=True, domain=[('state', '=', 'emitido')])

    # Datos heredados (related)
    no_auditoria = fields.Char(related='plan_id.clave', string='No. Auditoría', store=True)
    tipo = fields.Selection(related='plan_id.tipo', string='Tipo de auditoría')
    fecha_ejecucion = fields.Date(related='plan_id.fecha_inicio', string='Fecha de ejecución')
    fecha_ejecucion_fin = fields.Date(related='plan_id.fecha_fin', string='Hasta')
    lider_plan_id = fields.Many2one(related='plan_id.lider_id', string='Auditor Líder (plan)', store=True)

    # Datos propios
    area_proceso = fields.Char(string='Área / Proceso auditado')
    representante_auditado_id = fields.Many2one('res.users', string='Representante del auditado',
        domain=[('share', '=', False)])

    # ── REUNIÓN DE APERTURA ────────────────────────────────────────────────
    apertura_fecha = fields.Date(string='Fecha')
    apertura_hora_inicio = fields.Selection(_HORAS, string='Hora inicio')
    apertura_hora_fin = fields.Selection(_HORAS, string='Hora fin')
    apertura_lugar = fields.Char(string='Lugar')

    apertura_asistente_ids = fields.One2many('amunet.acta.asistente', 'acta_id',
        domain=[('seccion', '=', 'apertura')], string='Asistentes')

    # Agenda apertura
    aper_presentacion_equipo = fields.Boolean('Presentación del equipo auditor', default=True)
    aper_confirmacion_objetivo = fields.Boolean('Confirmación del objetivo de la auditoría', default=True)
    aper_confirmacion_alcance = fields.Boolean('Confirmación del alcance', default=True)
    aper_confirmacion_criterios = fields.Boolean('Confirmación de los criterios de auditoría', default=True)
    aper_presentacion_programa = fields.Boolean('Presentación del programa / cronograma', default=True)
    aper_confirmacion_disponibilidad = fields.Boolean(
        'Confirmación de disponibilidad (personal, instalaciones, docs.)', default=True)
    aper_canales_comunicacion = fields.Boolean('Acuerdo sobre canales de comunicación', default=True)
    aper_fecha_cierre = fields.Boolean('Acuerdo sobre fecha, hora y lugar de la reunión de cierre', default=True)
    aper_otros = fields.Char(string='Otros')

    apertura_observaciones = fields.Text(string='Observaciones / Comentarios del auditado')

    # ── REUNIÓN DE CIERRE ──────────────────────────────────────────────────
    cierre_fecha = fields.Date(string='Fecha')
    cierre_hora_inicio = fields.Selection(_HORAS, string='Hora inicio')
    cierre_hora_fin = fields.Selection(_HORAS, string='Hora fin')
    cierre_lugar = fields.Char(string='Lugar')

    cierre_asistente_ids = fields.One2many('amunet.acta.asistente', 'acta_id',
        domain=[('seccion', '=', 'cierre')], string='Asistentes')

    # Agenda cierre
    cier_agradecimiento = fields.Boolean('Agradecimiento por la colaboración', default=True)
    cier_resumen = fields.Boolean('Presentación del resumen de la auditoría', default=True)
    cier_hallazgos_aparte = fields.Boolean('Recordatorio: hallazgos detallados en formato aparte', default=True)
    cier_plazos_informe = fields.Boolean('Acuerdo de plazos para entrega del informe final', default=True)
    cier_plazos_pac = fields.Boolean('Acuerdo de plazos para presentación del PAC', default=True)
    cier_seguimiento = fields.Boolean('Acuerdo sobre fecha de seguimiento (si aplica)', default=False)
    cier_preguntas = fields.Boolean('Turno de preguntas y aclaraciones', default=True)
    cier_otros = fields.Char(string='Otros')

    cierre_observaciones = fields.Text(string='Observaciones y comentarios del auditado')
    cierre_compromiso_ids = fields.One2many('amunet.acta.compromiso', 'acta_id',
        domain=[('seccion', '=', 'cierre')], string='Compromisos')

    # ── FIRMAS ────────────────────────────────────────────────────────────
    firma_lider_id = fields.Many2one('res.users', string='Auditor Líder', readonly=True)
    fecha_firma_lider = fields.Date(string='Fecha', readonly=True)

    firma_auditado_id = fields.Many2one('res.users', string='Auditado', readonly=True)
    fecha_firma_auditado = fields.Date(string='Fecha', readonly=True)

    firma_sanitario_id = fields.Many2one('res.users', string='Responsable Sanitario', readonly=True)
    fecha_firma_sanitario = fields.Date(string='Fecha', readonly=True)

    puede_firmar_auditado = fields.Boolean(compute='_compute_puede_firmar_auditado')

    @api.depends('representante_auditado_id', 'firma_auditado_id')
    def _compute_puede_firmar_auditado(self):
        uid = self.env.user.id
        for r in self:
            r.puede_firmar_auditado = (
                uid == r.representante_auditado_id.id and not r.firma_auditado_id
            )

    # ── Secuencia ─────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('clave', _('Nuevo')) == _('Nuevo'):
                hoy = fields.Date.context_today(self)
                mm = hoy.strftime('%m')
                yy = hoy.strftime('%y')
                num = self.env['ir.sequence'].next_by_code('amunet.acta.auditoria') or '001'
                vals['clave'] = f'AC{mm}{yy}-{num}'
        return super().create(vals_list)

    # ── Firma electrónica ─────────────────────────────────────────────────

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_lider': _('Firma del Auditor Líder'),
            '_signature_auditado': _('Firma del Representante Auditado'),
            '_signature_sanitario': _('Firma del Responsable Sanitario'),
            '_signature_asistencia_apertura': _('Asistencia — Reunión de Apertura'),
            '_signature_asistencia_cierre': _('Asistencia — Reunión de Cierre'),
        }

    def action_firmar_lider(self):
        self.ensure_one()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_lider',
            _('Auditor Líder'),
            _('Firma del acta de auditoría %s.') % self.clave,
        )

    def _signature_lider(self):
        self.ensure_one()
        self.write({
            'firma_lider_id': self.env.user.id,
            'fecha_firma_lider': fields.Date.today(),
            'state': 'firmado',
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_firmar_auditado(self):
        self.ensure_one()
        uid = self.env.user.id
        if self.representante_auditado_id and uid != self.representante_auditado_id.id:
            raise ValidationError(_('Solo el representante del auditado puede firmar aquí.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_auditado',
            _('Representante Auditado'),
            _('Firma del auditado — acta %s.') % self.clave,
        )

    def _signature_auditado(self):
        self.ensure_one()
        self.write({
            'firma_auditado_id': self.env.user.id,
            'fecha_firma_auditado': fields.Date.today(),
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_firmar_sanitario(self):
        self.ensure_one()
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_sanitario',
            _('Responsable Sanitario'),
            _('Firma del responsable sanitario — acta %s.') % self.clave,
        )

    def _signature_sanitario(self):
        self.ensure_one()
        self.write({
            'firma_sanitario_id': self.env.user.id,
            'fecha_firma_sanitario': fields.Date.today(),
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_asistir_apertura(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Registrar asistencia — Apertura'),
            'res_model': 'amunet.acta.asistencia.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_acta_id': self.id,
                'default_seccion': 'apertura',
            },
        }

    def action_asistir_cierre(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Registrar asistencia — Cierre'),
            'res_model': 'amunet.acta.asistencia.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_acta_id': self.id,
                'default_seccion': 'cierre',
            },
        }

    def action_borrador(self):
        self.write({
            'state': 'borrador',
            'firma_lider_id': False, 'fecha_firma_lider': False,
            'firma_auditado_id': False, 'fecha_firma_auditado': False,
            'firma_sanitario_id': False, 'fecha_firma_sanitario': False,
        })


class AmunetActaAsistente(models.Model):
    _name = 'amunet.acta.asistente'
    _description = 'Asistente a reunión de auditoría'
    _order = 'acta_id, seccion, fecha, id'

    acta_id = fields.Many2one('amunet.acta.auditoria', required=True, ondelete='cascade')
    seccion = fields.Selection([
        ('apertura', 'Apertura'),
        ('cierre', 'Cierre'),
    ], required=True, default='apertura')
    user_id = fields.Many2one('res.users', string='Usuario', required=True, readonly=True)
    nombre = fields.Char(related='user_id.name', string='Nombre', store=True)
    fecha = fields.Date(string='Fecha de firma', readonly=True)
    cargo_rol = fields.Char(string='Cargo / Rol')
    empresa_area = fields.Char(string='Empresa / Área')


class AmunetActaCompromiso(models.Model):
    _name = 'amunet.acta.compromiso'
    _description = 'Compromiso acordado en reunión de auditoría'
    _order = 'acta_id, seccion, id'

    acta_id = fields.Many2one('amunet.acta.auditoria', required=True, ondelete='cascade')
    seccion = fields.Selection([
        ('apertura', 'Apertura'),
        ('cierre', 'Cierre'),
    ], required=True, default='apertura')
    descripcion = fields.Char(string='Compromiso', required=True)
    responsable = fields.Char(string='Responsable')
    fecha_limite = fields.Date(string='Fecha límite')
