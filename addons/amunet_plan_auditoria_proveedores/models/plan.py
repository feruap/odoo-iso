from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_TIPO = [
    ('inicial',       'Inicial'),
    ('seguimiento',   'Seguimiento'),
    ('extraordinaria','Extraordinaria'),
    ('renovacion',    'Renovación'),
]

_DEFAULT_OBJETIVO = (
    "Evaluar el Sistema de Gestión de Calidad del proveedor para verificar su cumplimiento "
    "con los requisitos establecidos en la norma ISO 13485:2016, el Reglamento (UE) 2017/746 (IVDR) "
    "y los requisitos específicos del fabricante, con el fin de determinar su capacidad para "
    "suministrar materias primas, componentes o servicios que cumplan con las especificaciones de "
    "calidad, seguridad y rendimiento exigidos para la fabricación de pruebas rápidas de diagnóstico."
)

_DEFAULT_ALCANCE = (
    "La presente auditoría cubre la verificación del Sistema de Gestión de Calidad del proveedor "
    "en los siguientes procesos y áreas:\n"
    "- Gestión de Calidad y Sistema Documental\n"
    "- Gestión de Riesgos (ISO 14971)\n"
    "- Diseño y Desarrollo (si aplica)\n"
    "- Compras y Gestión de Subcontratistas\n"
    "- Procesos Productivos y Control de Fabricación\n"
    "- Control de Calidad y Ensayos (incluyendo validación de métodos)\n"
    "- Almacenamiento, Conservación y Distribución\n"
    "- Gestión de Quejas, CAPA y Vigilancia Posterior a la Comercialización\n"
    "- Formación y Competencia del Personal"
)

_DEFAULT_CRIT_NORMATIVA = (
    "- Reglamento (UE) 2017/746 (IVDR) - Requisitos Generales de Seguridad y Rendimiento\n"
    "- ISO 13485:2016 - Sistemas de Gestión de Calidad para Dispositivos Médicos\n"
    "- ISO 14971:2019 - Gestión de Riesgos"
)

_DEFAULT_CRIT_FABRICANTE = (
    "- Especificaciones técnicas y de compra\n"
    "- Requisitos de calidad acordados en el contrato\n"
    "- Criterios de aceptación de materiales"
)

_DEFAULT_CRIT_PROVEEDOR = (
    "- Manual de Calidad\n"
    "- Procedimientos e instrucciones de trabajo\n"
    "- Especificaciones de producto\n"
    "- Registros del Sistema de Gestión de Calidad"
)


class AmunetPlanAuditoriaProveedor(models.Model):
    _name = 'amunet.plan.audit.prov'
    _description = 'Plan de Auditoría de Proveedores (F-DC-005-016)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_emision desc, id desc'
    _rec_name = 'clave'

    clave = fields.Char(string='No. Auditoría', readonly=True, copy=False,
                        default=lambda self: _('Nuevo'))
    fecha_emision   = fields.Date(string='Fecha de emisión', default=fields.Date.today, required=True)
    norma           = fields.Char(string='Norma por aplicar',
                                  default='ISO 13485:2016, IVDR (UE) 2017/746')
    tipo            = fields.Selection(_TIPO, string='Tipo de auditoría', required=True,
                                       default='inicial', tracking=True)
    proveedor       = fields.Char(string='Nombre del proveedor', required=True)
    fecha_inicio    = fields.Date(string='Fecha inicio de auditoría', required=True)
    fecha_fin       = fields.Date(string='Fecha fin de auditoría')
    lider_id        = fields.Many2one('res.users', string='Auditor Líder', required=True)
    auditor_ids     = fields.Many2many('res.users', 'plan_audit_prov_auditor_rel',
                                       'plan_id', 'user_id', string='Auditores internos')
    acompanante     = fields.Char(string='Acompañante del proveedor (nombre y cargo)')

    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('vigente',  'Vigente'),
        ('cerrado',  'Cerrado'),
    ], default='borrador', string='Estado', required=True, tracking=True)

    # ── 2. Objetivo ──────────────────────────────────────────────────────────
    objetivo    = fields.Text(string='Objetivo', default=_DEFAULT_OBJETIVO)

    # ── 3. Alcance ───────────────────────────────────────────────────────────
    alcance     = fields.Text(string='Alcance', default=_DEFAULT_ALCANCE)
    exclusiones = fields.Char(string='Exclusiones')

    # ── 4. Criterios ─────────────────────────────────────────────────────────
    criterios_normativa  = fields.Text(string='Normativa externa',   default=_DEFAULT_CRIT_NORMATIVA)
    criterios_fabricante = fields.Text(string='Documentación del fabricante', default=_DEFAULT_CRIT_FABRICANTE)
    criterios_proveedor  = fields.Text(string='Documentación interna del proveedor', default=_DEFAULT_CRIT_PROVEEDOR)

    # ── 5. Metodología ───────────────────────────────────────────────────────
    met_apertura    = fields.Boolean('Reunión de apertura',               default=True)
    met_entrevistas = fields.Boolean('Entrevistas con personal clave',    default=True)
    met_revision    = fields.Boolean('Revisión documental',               default=True)
    met_verificacion= fields.Boolean('Verificación in situ',             default=True)
    met_muestreo    = fields.Boolean('Muestreo de registros',             default=True)
    met_observacion = fields.Boolean('Observación directa',               default=False)
    met_cierre      = fields.Boolean('Reunión de cierre',                 default=True)

    # ── 6. Áreas a auditar ───────────────────────────────────────────────────
    area_ids        = fields.One2many('amunet.plan.audit.prov.area', 'plan_id', string='Áreas a auditar')

    # ── 7. Cronograma ────────────────────────────────────────────────────────
    cronograma_ids  = fields.One2many('amunet.plan.audit.prov.dia', 'plan_id', string='Cronograma')

    # ── 10. Plazos ───────────────────────────────────────────────────────────
    plazo_preliminar         = fields.Integer('Informe preliminar (días hábiles)',   default=5)
    plazo_revision_proveedor = fields.Integer('Revisión por el proveedor (días hábiles)', default=10)
    plazo_final              = fields.Integer('Informe final (días hábiles)',         default=15)
    plazo_pac                = fields.Integer('Plan de acciones correctivas (días hábiles)', default=30)

    # ── 11. Lista de asistencia ──────────────────────────────────────────────
    asistente_ids   = fields.One2many('amunet.plan.audit.prov.asistente', 'plan_id',
                                      string='Lista de asistencia')

    # ── 13. Distribución ─────────────────────────────────────────────────────
    dist_archivo  = fields.Boolean('Archivo de Auditorías de Proveedores', default=True)
    dist_calidad  = fields.Boolean('Responsable de Calidad (fabricante)',  default=True)
    dist_compras  = fields.Boolean('Responsable de Compras (fabricante)',  default=True)
    dist_proveedor= fields.Boolean('Proveedor auditado',                   default=True)
    dist_otros    = fields.Char('Otros destinatarios')

    # ── 14. Observaciones ────────────────────────────────────────────────────
    observaciones = fields.Text(string='Observaciones')

    # ── 12. Firmas / Aprobaciones ────────────────────────────────────────────
    elaboro_id           = fields.Many2one('res.users', string='Auditor Líder (firma)', readonly=True)
    fecha_elaboro        = fields.Date(string='Fecha firma líder',  readonly=True)
    resp_calidad_prov    = fields.Char(string='Responsable de Calidad del proveedor')
    firma_compras_id     = fields.Many2one('res.users', string='Firmó — Resp. de Compras',
                                           readonly=True)
    fecha_firma_compras  = fields.Date(string='Fecha firma compras', readonly=True)

    # ── Secuencia ────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('clave', _('Nuevo')) == _('Nuevo'):
                vals['clave'] = self.env['ir.sequence'].next_by_code(
                    'amunet.plan.audit.prov') or _('Nuevo')
        return super().create(vals_list)

    # ── Firma electrónica ────────────────────────────────────────────────────
    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_lider':   _('Firma del Auditor Líder — Plan de Auditoría de Proveedores'),
            '_signature_compras': _('Firma del Responsable de Compras — Plan de Auditoría de Proveedores'),
        }

    def action_firmar_lider(self):
        self.ensure_one()
        if self.elaboro_id:
            raise ValidationError(_('El Auditor Líder ya firmó este plan.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_lider',
            _('Auditor Líder'),
            _('Firma de elaboración del plan %s.') % self.clave,
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
            raise ValidationError(_('Responsable de Compras ya firmó este plan.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_compras',
            _('Responsable de Compras'),
            _('Firma de aprobación del plan %s.') % self.clave,
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
            raise ValidationError(_('Solo el gestor de documentos puede eliminar este plan.'))
        return super().unlink()


class AmunetPlanAuditProvArea(models.Model):
    _name = 'amunet.plan.audit.prov.area'
    _description = 'Área a auditar — Plan de Auditoría de Proveedores'
    _order = 'plan_id, secuencia, id'

    plan_id    = fields.Many2one('amunet.plan.audit.prov', required=True, ondelete='cascade')
    secuencia  = fields.Integer(default=10)
    codigo     = fields.Char(string='Código', placeholder='P-01')
    area       = fields.Char(string='Área / Proceso', required=True)
    responsable= fields.Char(string='Responsable')
    duracion   = fields.Char(string='Duración', placeholder='1.5 h')


class AmunetPlanAuditProvDia(models.Model):
    _name = 'amunet.plan.audit.prov.dia'
    _description = 'Cronograma — Plan de Auditoría de Proveedores'
    _order = 'plan_id, secuencia, id'

    plan_id            = fields.Many2one('amunet.plan.audit.prov', required=True, ondelete='cascade')
    secuencia          = fields.Integer(default=10)
    dia                = fields.Char(string='Día', placeholder='Día 1')
    hora               = fields.Char(string='Hora', placeholder='09:00 - 09:30')
    actividad          = fields.Char(string='Actividad', required=True)
    area               = fields.Char(string='Área / Código')
    auditor_responsable= fields.Char(string='Auditor responsable')


class AmunetPlanAuditProvAsistente(models.Model):
    _name = 'amunet.plan.audit.prov.asistente'
    _description = 'Lista de asistencia — Plan de Auditoría de Proveedores'
    _order = 'plan_id, no, id'

    plan_id     = fields.Many2one('amunet.plan.audit.prov', required=True, ondelete='cascade')
    no          = fields.Integer(string='No.')
    fecha       = fields.Date(string='Fecha')
    nombre      = fields.Char(string='Nombre')
    empresa_area= fields.Char(string='Empresa / Área')
