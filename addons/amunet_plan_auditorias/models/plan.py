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


class AmunetPlanAuditoria(models.Model):
    _name = 'amunet.plan.auditoria'
    _description = 'Plan de Auditoría Interna'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_inicio desc, clave'
    _rec_name = 'clave'

    clave = fields.Char(string='Clave', readonly=True, copy=False,
        default=lambda self: _('Nuevo'))
    tipo = fields.Selection([
        ('programada', 'Programada'),
        ('no_programada', 'No Programada'),
        ('reprogramada', 'Reprogramada'),
    ], string='Tipo de auditoría', required=True, default='programada')
    modalidad = fields.Selection([
        ('primera', 'Primera parte (interna)'),
        ('segunda', 'Segunda parte (cliente/proveedor)'),
        ('tercera', 'Tercera parte (certificación/regulatoria)'),
    ], string='Modalidad', default='primera')
    fecha_inicio = fields.Date(string='Fecha de auditoría', required=True)
    fecha_fin = fields.Date(string='Fecha de término')
    sitio = fields.Char(string='Sitio')
    objetivos = fields.Text(string='Objetivos de la auditoría')
    alcance = fields.Text(string='Alcance de la auditoría')
    limitaciones = fields.Text(string='Limitaciones / Exclusiones')
    cambios = fields.Text(string='Cambios al plan')

    # Metodología
    met_apertura = fields.Boolean(string='Reunión de apertura', default=True)
    met_entrevistas = fields.Boolean(string='Entrevistas con personal clave', default=True)
    met_revision_doc = fields.Boolean(string='Revisión documental', default=True)
    met_verificacion = fields.Boolean(string='Verificación in situ', default=True)
    met_muestreo = fields.Boolean(string='Muestreo de registros', default=True)
    met_observacion = fields.Boolean(string='Observación directa', default=False)
    met_cierre = fields.Boolean(string='Reunión de cierre', default=True)

    # Plazos del informe (días hábiles)
    plazo_preliminar = fields.Integer(string='Informe preliminar', default=5)
    plazo_revision_auditado = fields.Integer(string='Revisión del auditado', default=10)
    plazo_informe_final = fields.Integer(string='Informe final', default=15)
    plazo_plan_capa = fields.Integer(string='Plan de acciones correctivas', default=30)

    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('emitido', 'Emitido'),
        ('cerrado', 'Cerrado'),
    ], default='borrador', string='Estado', required=True, tracking=True)

    # Convocatoria de referencia
    convocatoria_id = fields.Many2one(
        'amunet.auditor.convocatoria', string='Convocatoria de referencia',
        domain=[('state', '=', 'cerrada')])

    # Equipo auditor
    lider_id = fields.Many2one('res.users', string='Auditor líder',
        domain=[('share', '=', False)])
    auditor_ids = fields.Many2many('res.users', 'plan_auditoria_auditor_rel',
        'plan_id', 'user_id', string='Auditores', domain=[('share', '=', False)])
    observador_ids = fields.Many2many('res.users', 'plan_auditoria_observador_rel',
        'plan_id', 'user_id', string='Observadores', domain=[('share', '=', False)])
    experto_ids = fields.Many2many('res.users', 'plan_auditoria_experto_rel',
        'plan_id', 'user_id', string='Expertos técnicos', domain=[('share', '=', False)])

    # Criterios y agenda
    criterio_ids = fields.One2many('amunet.plan.auditoria.criterio', 'plan_id', string='Criterios')
    info_ids = fields.One2many('amunet.plan.auditoria.info', 'plan_id', string='Información requerida')
    dia_ids = fields.One2many('amunet.plan.auditoria.dia', 'plan_id', string='Agenda por días')

    # Firmas
    elaboro_id = fields.Many2one('res.users', string='Elaboró', readonly=True)
    fecha_elaboro = fields.Date(string='Fecha elaboración', readonly=True)
    reviso_id = fields.Many2one('res.users', string='Revisó', readonly=True)
    fecha_reviso = fields.Date(string='Fecha revisión', readonly=True)
    autorizo_id = fields.Many2one('res.users', string='Autorizó', readonly=True)
    fecha_autorizo = fields.Date(string='Fecha autorización', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('clave', _('Nuevo')) == _('Nuevo'):
                fecha = vals.get('fecha_inicio')
                if fecha:
                    if isinstance(fecha, str):
                        fecha = fields.Date.from_string(fecha)
                    mm = fecha.strftime('%m')
                    yy = fecha.strftime('%y')
                else:
                    hoy = fields.Date.context_today(self)
                    mm = hoy.strftime('%m')
                    yy = hoy.strftime('%y')
                num = self.env['ir.sequence'].next_by_code('amunet.plan.auditoria') or '001'
                vals['clave'] = f'AI{mm}{yy}-{num}'
        return super().create(vals_list)

    # ── Firma electrónica ──────────────────────────────────────────────────────

    def _amunet_signature_allowed_methods(self):
        return {
            '_signature_elaborar': _('Elaboración del plan de auditoría'),
            '_signature_revisar': _('Revisión del plan de auditoría'),
            '_signature_autorizar': _('Autorización y emisión del plan de auditoría'),
        }

    def action_firmar_elaboracion(self):
        self.ensure_one()
        if self.state != 'borrador':
            raise ValidationError(_('Solo se puede firmar la elaboración en estado Borrador.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_elaborar',
            _('Elaboró'),
            _('Firma de elaboración del plan %s.') % self.clave,
        )

    def _signature_elaborar(self):
        self.ensure_one()
        self.write({'elaboro_id': self.env.user.id, 'fecha_elaboro': fields.Date.today()})
        return {'type': 'ir.actions.act_window_close'}

    def action_firmar_revision(self):
        self.ensure_one()
        if self.state != 'borrador':
            raise ValidationError(_('Solo se puede firmar la revisión en estado Borrador.'))
        if not self.elaboro_id:
            raise ValidationError(_('Firma primero la elaboración antes de revisar.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_revisar',
            _('Responsable de calidad del auditado'),
            _('Firma de revisión del plan %s.') % self.clave,
        )

    def _signature_revisar(self):
        self.ensure_one()
        self.write({'reviso_id': self.env.user.id, 'fecha_reviso': fields.Date.today()})
        return {'type': 'ir.actions.act_window_close'}

    def action_firmar_autorizacion(self):
        self.ensure_one()
        if self.state != 'borrador':
            raise ValidationError(_('Solo se puede autorizar en estado Borrador.'))
        if not self.reviso_id:
            raise ValidationError(_('Firma primero la revisión antes de autorizar.'))
        return self.env['amunet.generic.signature.wizard'].open_for(
            self, '_signature_autorizar',
            _('Autorizó (Gerencia)'),
            _('Autorización y emisión del plan %s.') % self.clave,
        )

    def _signature_autorizar(self):
        self.ensure_one()
        self.write({
            'autorizo_id': self.env.user.id,
            'fecha_autorizo': fields.Date.today(),
            'state': 'emitido',
        })
        return {'type': 'ir.actions.act_window_close'}

    # ── Acciones de estado ─────────────────────────────────────────────────────

    def action_cerrar(self):
        self.write({'state': 'cerrado'})

    def action_borrador(self):
        self.write({
            'state': 'borrador',
            'elaboro_id': False, 'fecha_elaboro': False,
            'reviso_id': False, 'fecha_reviso': False,
            'autorizo_id': False, 'fecha_autorizo': False,
        })

    def action_cargar_equipo(self):
        self.ensure_one()
        if not self.convocatoria_id:
            raise ValidationError(_('Selecciona primero una convocatoria de referencia.'))
        seleccionados = self.convocatoria_id.candidato_ids.filtered(
            lambda c: c.estado == 'seleccionado')
        if not seleccionados:
            raise ValidationError(
                _('La convocatoria seleccionada no tiene candidatos en estado Seleccionado.'))
        lider = seleccionados.filtered('es_lider')
        auditores = seleccionados.filtered(
            lambda c: not c.es_lider and c.tipo_auditor == 'interno')
        formacion = seleccionados.filtered(
            lambda c: not c.es_lider and c.tipo_auditor == 'formacion')
        vals = {}
        if lider:
            vals['lider_id'] = lider[0].usuario_id.id
        if auditores:
            vals['auditor_ids'] = [(6, 0, auditores.mapped('usuario_id').ids)]
        if formacion:
            vals['observador_ids'] = [(6, 0, formacion.mapped('usuario_id').ids)]
        self.write(vals)

    def action_agregar_dia(self):
        self.ensure_one()
        nuevo_dia = self.env['amunet.plan.auditoria.dia'].create({
            'plan_id': self.id,
            'fecha': self.fecha_inicio,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Agenda del día',
            'res_model': 'amunet.plan.auditoria.dia',
            'view_mode': 'form',
            'res_id': nuevo_dia.id,
            'target': 'new',
        }

    def unlink(self):
        if any(r.state != 'borrador' for r in self):
            raise ValidationError(
                _('Solo se pueden eliminar planes en estado Borrador.'))
        return super().unlink()


class AmunetPlanAuditoriaCriterio(models.Model):
    _name = 'amunet.plan.auditoria.criterio'
    _description = 'Criterio de auditoría'
    _order = 'plan_id, secuencia, id'

    plan_id = fields.Many2one('amunet.plan.auditoria', required=True, ondelete='cascade')
    secuencia = fields.Integer(default=10)
    codigo = fields.Char(string='ID', placeholder='C-01')
    nombre = fields.Char(string='Criterio', required=True)
    descripcion = fields.Text(string='Descripción')


class AmunetPlanAuditoriaInfo(models.Model):
    _name = 'amunet.plan.auditoria.info'
    _description = 'Información requerida para la auditoría'
    _order = 'plan_id, secuencia, id'

    plan_id = fields.Many2one('amunet.plan.auditoria', required=True, ondelete='cascade')
    secuencia = fields.Integer(default=10)
    concepto = fields.Char(string='Concepto', required=True)
    resultado = fields.Selection([('C', 'C'), ('NC', 'NC'), ('na', 'N/A')], string='Resultado')
    observaciones = fields.Char(string='Observaciones')


class AmunetPlanAuditoriaDia(models.Model):
    _name = 'amunet.plan.auditoria.dia'
    _description = 'Día de auditoría'
    _order = 'plan_id, fecha, id'

    plan_id = fields.Many2one('amunet.plan.auditoria', required=True, ondelete='cascade')
    fecha = fields.Date(string='Fecha', required=True)
    sitio = fields.Char(string='Sitio')
    turno = fields.Selection([
        ('matutino', 'Matutino'),
        ('vespertino', 'Vespertino'),
        ('nocturno', 'Nocturno'),
        ('unico', 'Único'),
    ], string='Turno')
    actividad_ids = fields.One2many('amunet.plan.auditoria.actividad', 'dia_id', string='Actividades')
    actividad_count = fields.Integer(compute='_compute_actividad_count', string='Actividades')

    def _compute_actividad_count(self):
        for r in self:
            r.actividad_count = len(r.actividad_ids)

    def action_abrir_agenda(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Agenda — %s' % (self.fecha or ''),
            'res_model': 'amunet.plan.auditoria.dia',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }


class AmunetPlanAuditoriaActividad(models.Model):
    _name = 'amunet.plan.auditoria.actividad'
    _description = 'Actividad de la agenda de auditoría'
    _order = 'dia_id, horario, id'

    dia_id = fields.Many2one('amunet.plan.auditoria.dia', required=True, ondelete='cascade')
    hora_inicio = fields.Selection(_HORAS, string='Inicio')
    hora_fin = fields.Selection(_HORAS, string='Fin')
    equipo_ids = fields.Many2many('res.users', compute='_compute_equipo_ids')
    auditor_id = fields.Many2one('res.users', string='Auditor', domain="[('id', 'in', equipo_ids)]")
    que_auditar = fields.Char(string='¿Qué se va a auditar?')
    requisitos = fields.Char(string='Requisitos')
    auditado_id = fields.Many2one('res.users', string='Auditado',
        domain=[('share', '=', False), ('active', '=', True)])

    def _compute_equipo_ids(self):
        todos = self.env['res.users'].search([('share', '=', False), ('active', '=', True)])
        for r in self:
            plan = r.dia_id.plan_id
            if plan:
                equipo = plan.lider_id | plan.auditor_ids | plan.observador_ids | plan.experto_ids
                r.equipo_ids = equipo if equipo else todos
            else:
                r.equipo_ids = todos
