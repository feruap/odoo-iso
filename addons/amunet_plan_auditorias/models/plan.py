from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AmunetPlanAuditoria(models.Model):
    _name = 'amunet.plan.auditoria'
    _description = 'Plan de Auditoría Interna'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_inicio desc, clave'
    _rec_name = 'clave'

    clave = fields.Char(
        string='Clave', readonly=True, copy=False,
        default=lambda self: _('Nuevo'))
    tipo = fields.Selection([
        ('programada', 'Programada'),
        ('no_programada', 'No Programada'),
        ('reprogramada', 'Reprogramada'),
    ], string='Tipo de auditoría', required=True, default='programada')
    fecha_inicio = fields.Date(string='Fecha de auditoría', required=True)
    fecha_fin = fields.Date(string='Fecha de término')
    criterios = fields.Text(string='Criterios')
    alcance = fields.Text(string='Alcance de la auditoría')
    turnos = fields.Selection([
        ('matutino', 'Matutino'),
        ('vespertino', 'Vespertino'),
        ('nocturno', 'Nocturno'),
        ('unico', 'Único'),
        ('todos', 'Todos'),
    ], string='Turno auditado')
    sitio = fields.Char(string='Sitio')
    domicilio = fields.Char(string='Domicilio')
    objetivos = fields.Text(string='Objetivos de la auditoría')
    cambios = fields.Text(string='Cambios al plan')
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('emitido', 'Emitido'),
        ('cerrado', 'Cerrado'),
    ], default='borrador', string='Estado', required=True, tracking=True)

    # Referencia a convocatoria
    convocatoria_id = fields.Many2one(
        'amunet.auditor.convocatoria', string='Convocatoria de referencia',
        domain=[('state', '=', 'cerrada')])

    # Equipo auditor
    lider_id = fields.Many2one(
        'res.users', string='Auditor líder',
        domain=[('share', '=', False)])
    auditor_ids = fields.Many2many(
        'res.users', 'plan_auditoria_auditor_rel',
        'plan_id', 'user_id',
        string='Auditores',
        domain=[('share', '=', False)])
    observador_ids = fields.Many2many(
        'res.users', 'plan_auditoria_observador_rel',
        'plan_id', 'user_id',
        string='Observadores',
        domain=[('share', '=', False)])
    experto_ids = fields.Many2many(
        'res.users', 'plan_auditoria_experto_rel',
        'plan_id', 'user_id',
        string='Expertos técnicos',
        domain=[('share', '=', False)])

    # Información requerida y agenda
    info_ids = fields.One2many(
        'amunet.plan.auditoria.info', 'plan_id', string='Información requerida')
    dia_ids = fields.One2many(
        'amunet.plan.auditoria.dia', 'plan_id', string='Agenda por días')

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

    def action_emitir(self):
        self.write({'state': 'emitido'})

    def action_cerrar(self):
        self.write({'state': 'cerrado'})

    def action_borrador(self):
        self.write({'state': 'borrador'})

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


class AmunetPlanAuditoriaInfo(models.Model):
    _name = 'amunet.plan.auditoria.info'
    _description = 'Información requerida para la auditoría'
    _order = 'plan_id, secuencia, id'

    plan_id = fields.Many2one(
        'amunet.plan.auditoria', required=True, ondelete='cascade')
    secuencia = fields.Integer(default=10)
    concepto = fields.Char(string='Concepto', required=True)
    resultado = fields.Selection([
        ('C', 'C'),
        ('NC', 'NC'),
        ('na', 'N/A'),
    ], string='Resultado')
    observaciones = fields.Char(string='Observaciones')


class AmunetPlanAuditoriaDia(models.Model):
    _name = 'amunet.plan.auditoria.dia'
    _description = 'Día de auditoría'
    _order = 'plan_id, fecha, id'

    plan_id = fields.Many2one(
        'amunet.plan.auditoria', required=True, ondelete='cascade')
    fecha = fields.Date(string='Fecha', required=True)
    sitio = fields.Char(string='Sitio')
    turno = fields.Selection([
        ('matutino', 'Matutino'),
        ('vespertino', 'Vespertino'),
        ('nocturno', 'Nocturno'),
        ('unico', 'Único'),
    ], string='Turno')
    actividad_ids = fields.One2many(
        'amunet.plan.auditoria.actividad', 'dia_id', string='Actividades')
    actividad_count = fields.Integer(
        compute='_compute_actividad_count', string='Actividades')

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

    dia_id = fields.Many2one(
        'amunet.plan.auditoria.dia', required=True, ondelete='cascade')
    horario = fields.Char(string='Horario', placeholder='08:00 – 09:00')
    auditor_id = fields.Many2one(
        'res.users', string='Auditor',
        domain=[('share', '=', False)])
    que_auditar = fields.Char(string='¿Qué se va a auditar?')
    requisitos = fields.Char(string='Requisitos')
    auditado = fields.Char(string='Auditado')
