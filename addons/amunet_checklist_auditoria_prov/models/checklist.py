from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

# ── Criterios precargados por tipo ──────────────────────────────────────────
# Tupla: (seccion_num, seccion_nombre, ponderacion, no, criterio)
# Cada ítem vale 2 puntos.

_CRITERIOS = {
    'critico': [
        (1, 'Documentación Legal y Regulatoria', 15.0, 1, 'Registro Federal de Contribuyentes (RFC)'),
        (1, 'Documentación Legal y Regulatoria', 15.0, 2, 'Aviso de Funcionamiento y Responsable Sanitario'),
        (1, 'Documentación Legal y Regulatoria', 15.0, 3, 'Licencia Sanitaria vigente'),
        (1, 'Documentación Legal y Regulatoria', 15.0, 4, 'Otros permisos (especificar)'),
        (2, 'Personal y Competencia', 15.0, 1, 'Cuenta con organigrama vigente'),
        (2, 'Personal y Competencia', 15.0, 2, 'Cuenta con perfiles de puesto documentados'),
        (2, 'Personal y Competencia', 15.0, 3, 'Cuenta con programa de capacitación anual'),
        (2, 'Personal y Competencia', 15.0, 4, 'Se realizan exámenes médicos al personal'),
        (2, 'Personal y Competencia', 15.0, 5, 'El personal cuenta con formación específica (manejo de reactivos, etc.)'),
        (2, 'Personal y Competencia', 15.0, 6, 'Existen registros de capacitación y competencia'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 1,  'Sistema de Gestión de Calidad certificado ISO 13485'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 2,  'Política de Calidad definida y comunicada'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 3,  'Manual de Calidad vigente'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 4,  'Procedimiento de Control de Documentación'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 5,  'Procedimiento de Control de Registros'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 6,  'Procedimiento de Auditorías Internas'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 7,  'Procedimiento de Gestión de Riesgos (ISO 14971)'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 8,  'Procedimiento de Homologación y evaluación de proveedores'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 9,  'Procedimiento de Gestión de No Conformidades y CAPA'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 10, 'Procedimiento de Control de Cambios'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 11, 'Procedimiento de Trazabilidad de productos'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 12, 'Procedimiento de Almacenamiento y conservación'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 13, 'Procedimiento de Reclamaciones de clientes'),
        (4, 'Requisitos Técnicos Específicos (IVDR)', 20.0, 1, 'Demuestra conocimiento del Reglamento (UE) 2017/746 (IVDR)'),
        (4, 'Requisitos Técnicos Específicos (IVDR)', 20.0, 2, 'Proporciona certificados de análisis (CoA) por lote'),
        (4, 'Requisitos Técnicos Específicos (IVDR)', 20.0, 3, 'Los materiales cuentan con especificaciones técnicas documentadas'),
        (4, 'Requisitos Técnicos Específicos (IVDR)', 20.0, 4, 'Gestiona cambios en materias primas con notificación previa'),
        (4, 'Requisitos Técnicos Específicos (IVDR)', 20.0, 5, 'Dispone de sistema de trazabilidad de lotes'),
        (4, 'Requisitos Técnicos Específicos (IVDR)', 20.0, 6, 'Garantiza condiciones de transporte y almacenamiento'),
        (4, 'Requisitos Técnicos Específicos (IVDR)', 20.0, 7, 'Realiza pruebas de estabilidad de materiales'),
        (4, 'Requisitos Técnicos Específicos (IVDR)', 20.0, 8, 'Proporciona hojas de datos de seguridad (MSDS)'),
        (5, 'Infraestructura y Equipos', 10.0, 1, 'Instalaciones adecuadas para el tipo de producto'),
        (5, 'Infraestructura y Equipos', 10.0, 2, 'Equipos calibrados periódicamente'),
        (5, 'Infraestructura y Equipos', 10.0, 3, 'Plan de mantenimiento preventivo'),
        (5, 'Infraestructura y Equipos', 10.0, 4, 'Control de condiciones ambientales (temperatura, humedad)'),
        (5, 'Infraestructura y Equipos', 10.0, 5, 'Áreas de almacenamiento adecuadas y organizadas'),
    ],
    'importante': [
        (1, 'Documentación Legal', 20.0, 1, 'Registro Federal de Contribuyentes (RFC)'),
        (1, 'Documentación Legal', 20.0, 2, 'Aviso de Funcionamiento'),
        (1, 'Documentación Legal', 20.0, 3, 'Licencia Sanitaria (si aplica)'),
        (2, 'Personal y Competencia', 20.0, 1, 'Cuenta con organigrama vigente'),
        (2, 'Personal y Competencia', 20.0, 2, 'Cuenta con perfiles de puesto documentados'),
        (2, 'Personal y Competencia', 20.0, 3, 'Cuenta con programa de capacitación acorde a actividades'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 1, 'Sistema de Gestión de Calidad (ISO 13485, si aplica)'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 2, 'Procedimiento de Control de Documentación'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 3, 'Procedimiento de Control de Registros'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 4, 'Procedimiento de No Conformidades y CAPA'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 5, 'Procedimiento de Control de Cambios'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 6, 'Trazabilidad de productos/servicios'),
        (3, 'Sistema de Gestión de Calidad', 40.0, 7, 'Procedimiento de Reclamaciones'),
        (4, 'Requisitos Específicos del Servicio', 20.0, 1, 'Cumple con los requisitos acordados en el contrato'),
        (4, 'Requisitos Específicos del Servicio', 20.0, 2, 'Registra y controla las condiciones del servicio'),
        (4, 'Requisitos Específicos del Servicio', 20.0, 3, 'Dispone de procedimientos para gestionar incidencias'),
        (4, 'Requisitos Específicos del Servicio', 20.0, 4, 'Proporciona evidencia de la ejecución del servicio'),
    ],
    'general': [
        (1, 'Documentación Legal', 50.0, 1, 'Registro Federal de Contribuyentes (RFC)'),
        (1, 'Documentación Legal', 50.0, 2, 'Aviso de Funcionamiento'),
        (1, 'Documentación Legal', 50.0, 3, 'Licencia Sanitaria (si aplica)'),
        (2, 'Referencias y Antecedentes', 50.0, 1, 'Cuenta con referencias de otros clientes'),
        (2, 'Referencias y Antecedentes', 50.0, 2, 'Ha cumplido con los plazos acordados'),
        (2, 'Referencias y Antecedentes', 50.0, 3, 'No se han presentado quejas o reclamaciones graves'),
        (2, 'Referencias y Antecedentes', 50.0, 4, 'Demuestra capacidad de respuesta ante incidencias'),
    ],
}


class AmunetChecklistAuditoriaProv(models.Model):
    _name = 'amunet.checklist.audit.prov'
    _description = 'Checklist de Auditoría Técnica a Proveedores (F-DC-005-018)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, id desc'
    _rec_name = 'clave'

    clave = fields.Char(string='No. Checklist', readonly=True, copy=False,
                        default=lambda self: _('Nuevo'))
    plan_id       = fields.Many2one('amunet.plan.audit.prov', string='Plan de auditoría relacionado',
                                    ondelete='set null')
    proveedor     = fields.Char(string='Proveedor', required=True)
    fecha         = fields.Date(string='Fecha', default=fields.Date.today, required=True)
    lider_id      = fields.Many2one('res.users', string='Auditor', required=True)
    no_auditoria  = fields.Char(string='No. de auditoría')
    tipo_proveedor = fields.Selection([
        ('critico',    'Proveedor Crítico'),
        ('importante', 'Proveedor Importante'),
        ('general',    'Proveedor General'),
    ], string='Tipo de proveedor', required=True, tracking=True)
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('vigente',  'Vigente'),
        ('cerrado',  'Cerrado'),
    ], default='borrador', string='Estado', required=True, tracking=True)

    # ── Datos extra (solo General) ───────────────────────────────────────────
    gen_razon_social    = fields.Char(string='Razón social')
    gen_producto        = fields.Char(string='Producto / Servicio')
    gen_contacto        = fields.Char(string='Contacto')
    gen_telefono        = fields.Char(string='Teléfono')
    gen_correo          = fields.Char(string='Correo')
    gen_anos_experiencia= fields.Char(string='Años de experiencia')
    gen_antiguedad      = fields.Char(string='Antigüedad en el mercado')

    # ── Criterios ────────────────────────────────────────────────────────────
    linea_ids = fields.One2many('amunet.checklist.audit.prov.linea', 'checklist_id',
                                string='Criterios de evaluación')

    # ── Hallazgos ────────────────────────────────────────────────────────────
    hallazgo_ids = fields.One2many('amunet.checklist.audit.prov.hallazgo', 'checklist_id',
                                   string='Hallazgos')
    accion_ids   = fields.One2many('amunet.checklist.audit.prov.accion', 'checklist_id',
                                   string='Acciones correctivas')
    fecha_seguimiento = fields.Date(string='Fecha de seguimiento')

    # ── Resultados (computed) ────────────────────────────────────────────────
    puntos_obtenidos  = fields.Integer(string='Puntos obtenidos',  compute='_compute_resultado', store=True)
    puntos_posibles   = fields.Integer(string='Puntos posibles',   compute='_compute_resultado', store=True)
    porcentaje        = fields.Float(string='% Cumplimiento',      compute='_compute_resultado', store=True, digits=(5, 1))
    conclusion_auto   = fields.Selection([
        ('aprobado',    'Aprobado'),
        ('condicionado','Condicionado'),
        ('rechazado',   'Rechazado'),
    ], string='Resultado', compute='_compute_resultado', store=True)
    justificacion     = fields.Text(string='Justificación')
    observaciones_gen = fields.Text(string='Observaciones')

    # ── Firmas ───────────────────────────────────────────────────────────────
    elaboro_id          = fields.Many2one('res.users', string='Auditor Líder (firma)', readonly=True)
    fecha_elaboro       = fields.Date(string='Fecha firma líder', readonly=True)
    resp_calidad_prov   = fields.Char(string='Responsable de Calidad del proveedor')
    firma_compras_id    = fields.Many2one('res.users', string='Firmó — Resp. de Compras', readonly=True)
    fecha_firma_compras = fields.Date(string='Fecha firma compras', readonly=True)

    # ── Computed ─────────────────────────────────────────────────────────────
    @api.depends('linea_ids.cumple', 'linea_ids.puntos_posibles')
    def _compute_resultado(self):
        for rec in self:
            lines = rec.linea_ids
            posibles  = sum(l.puntos_posibles for l in lines if l.cumple != 'na')
            obtenidos = sum(l.puntos_posibles for l in lines if l.cumple == 'si')
            rec.puntos_posibles  = posibles
            rec.puntos_obtenidos = obtenidos
            rec.porcentaje = (obtenidos / posibles * 100) if posibles else 0.0
            pct = rec.porcentaje
            if pct >= 86:
                rec.conclusion_auto = 'aprobado'
            elif pct >= 65:
                rec.conclusion_auto = 'condicionado'
            else:
                rec.conclusion_auto = 'rechazado'

    # ── Onchange: carga criterios según tipo ─────────────────────────────────
    @api.onchange('tipo_proveedor')
    def _onchange_tipo_proveedor(self):
        if not self.tipo_proveedor:
            return
        self.linea_ids = [(5, 0, 0)]  # borrar existentes
        criterios = _CRITERIOS.get(self.tipo_proveedor, [])
        nuevas = []
        for secnum, secnombre, pond, no, criterio in criterios:
            nuevas.append((0, 0, {
                'seccion_num':    secnum,
                'seccion_nombre': secnombre,
                'ponderacion':    pond,
                'no':             no,
                'criterio':       criterio,
                'cumple':         'no',
                'puntos_posibles': 2,
            }))
        self.linea_ids = nuevas

    # ── Secuencia ────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('clave', _('Nuevo')) == _('Nuevo'):
                vals['clave'] = self.env['ir.sequence'].next_by_code(
                    'amunet.checklist.audit.prov') or _('Nuevo')
        return super().create(vals_list)

    # ── Firmas PIN ────────────────────────────────────────────────────────────
    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_lider':   _('Firma del Auditor — Checklist Auditoría Técnica'),
            '_signature_compras': _('Firma del Resp. de Compras — Checklist Auditoría Técnica'),
        }

    def action_firmar_lider(self):
        self.ensure_one()
        if self.elaboro_id:
            raise ValidationError(_('El Auditor ya firmó este checklist.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_lider', _('Auditor Líder'),
            _('Firma de elaboración del checklist %s.') % self.clave,
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
            raise ValidationError(_('El Auditor debe firmar primero.'))
        if self.firma_compras_id:
            raise ValidationError(_('Responsable de Compras ya firmó.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_compras', _('Responsable de Compras'),
            _('Firma de aprobación del checklist %s.') % self.clave,
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
            'state': 'borrador',
            'elaboro_id': False, 'fecha_elaboro': False,
            'firma_compras_id': False, 'fecha_firma_compras': False,
        })

    def unlink(self):
        if not self.env.user.has_group('amunet_documentos.group_documentos_manager'):
            raise ValidationError(_('Solo el gestor de documentos puede eliminar este checklist.'))
        return super().unlink()


class AmunetChecklistLinea(models.Model):
    _name = 'amunet.checklist.audit.prov.linea'
    _description = 'Criterio — Checklist Auditoría Técnica a Proveedores'
    _order = 'checklist_id, seccion_num, no'

    checklist_id    = fields.Many2one('amunet.checklist.audit.prov', required=True, ondelete='cascade')
    seccion_num     = fields.Integer(string='Sección', default=1)
    seccion_nombre  = fields.Char(string='Nombre de sección')
    ponderacion     = fields.Float(string='Ponderación (%)', digits=(5, 1))
    no              = fields.Integer(string='Nº')
    criterio        = fields.Char(string='Criterio')
    cumple          = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A'),
    ], string='Cumple', default='no', required=True)
    observaciones   = fields.Char(string='Observaciones')
    puntos_posibles = fields.Integer(string='Pts.', default=2)


class AmunetChecklistHallazgo(models.Model):
    _name = 'amunet.checklist.audit.prov.hallazgo'
    _description = 'Hallazgo — Checklist Auditoría Técnica a Proveedores'
    _order = 'checklist_id, tipo, id'

    checklist_id = fields.Many2one('amunet.checklist.audit.prov', required=True, ondelete='cascade')
    tipo = fields.Selection([
        ('nc_mayor',     'No Conformidad Mayor'),
        ('nc_menor',     'No Conformidad Menor'),
        ('observacion',  'Observación / Oportunidad de Mejora'),
    ], string='Tipo', required=True, default='nc_menor')
    descripcion            = fields.Char(string='Descripción', required=True)
    evidencia              = fields.Char(string='Evidencia / Recomendación')


class AmunetChecklistAccion(models.Model):
    _name = 'amunet.checklist.audit.prov.accion'
    _description = 'Acción Correctiva — Checklist Auditoría Técnica a Proveedores'
    _order = 'checklist_id, id'

    checklist_id = fields.Many2one('amunet.checklist.audit.prov', required=True, ondelete='cascade')
    nc_asociada     = fields.Char(string='NC Asociada')
    accion          = fields.Char(string='Acción Correctiva', required=True)
    responsable     = fields.Char(string='Responsable')
    fecha_limite    = fields.Date(string='Fecha Límite')
