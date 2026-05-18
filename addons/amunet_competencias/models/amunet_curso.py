# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class AmunetCurso(models.Model):
    """
    Curso de capacitacion. Reune en una sola ficha el contenido (videos,
    material escrito, PDFs) y el examen. Al aprobar el examen se genera
    automaticamente un registro de capacitacion vigente.

    ISO 13485:2016 - Clausula 6.2 (Competencia del personal).
    """
    _name = 'amunet.curso'
    _description = 'Curso de Capacitacion (ISO 13485 6.2)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Nombre del Curso', required=True, tracking=True)
    code = fields.Char(string='Codigo', readonly=True, copy=False, default='Nuevo')
    active = fields.Boolean(default=True)

    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('publicado', 'Publicado'),
    ], string='Estado', default='borrador', required=True, tracking=True,
        help='Solo los cursos Publicados aparecen en "Mis Cursos" y pueden presentarse.')

    descripcion = fields.Html(
        string='Contenido escrito', sanitize=True,
        help='Material escrito del curso: instrucciones, teoria, resumen del PNO.')

    video_ids = fields.One2many(
        'amunet.curso.video', 'curso_id', string='Videos del curso',
        help='Uno o varios videos, en orden. YouTube y Vimeo se reproducen '
             'embebidos dentro de la pagina.')
    video_count = fields.Integer(
        string='No. de videos', compute='_compute_video_count')

    material_ids = fields.Many2many(
        'ir.attachment',
        'amunet_curso_material_rel', 'curso_id', 'attachment_id',
        string='Material de apoyo (PDFs)',
        help='Archivos PDF u otros documentos de apoyo del curso.')

    procedure_ids = fields.Many2many(
        'amunet.quality.procedure',
        'amunet_curso_procedure_rel', 'curso_id', 'procedure_id',
        string='PNOs que cubre',
        domain=[('active', '=', True)],
        help='Procedimientos (PNOs) que acredita este curso. Al aprobar el examen '
             'se genera un registro de capacitacion vigente para cada uno. Los PNOs '
             'tambien conectan el curso con las maquinas que los usan.')

    departamento_ids = fields.Many2many(
        'hr.department',
        'amunet_curso_department_rel', 'curso_id', 'department_id',
        string='Departamentos asignados',
        help='Departamentos cuyos empleados deben tomar este curso. '
             'Si se deja vacio, el curso aplica a todos los empleados.')

    validez_meses = fields.Integer(
        string='Vigencia (meses)', default=12, required=True,
        help='Meses de vigencia del registro de capacitacion que se genera al '
             'aprobar. 0 = sin vencimiento.')

    calificacion_minima = fields.Float(
        string='Calificacion minima (%)', default=80.0, required=True,
        help='Porcentaje minimo de aciertos para aprobar el examen.')

    tiempo_minimo_estudio = fields.Integer(
        string='Tiempo minimo de estudio (min)', default=0,
        help='Minutos que el empleado debe dedicar al contenido antes de poder '
             'presentar el examen. 0 = sin minimo.')
    tiempo_limite_examen = fields.Integer(
        string='Tiempo limite del examen (min)', default=0,
        help='Minutos maximos para presentar el examen una vez iniciado. '
             '0 = sin limite.')

    revision_requerida = fields.Boolean(
        string='Revision requerida', default=False, tracking=True,
        help='Se marca automaticamente cuando cambia la version de un PNO '
             'vinculado. Indica que el contenido y el examen deben revisarse.')
    revision_motivo = fields.Char(string='Motivo de revision', readonly=True)

    pregunta_ids = fields.One2many(
        'amunet.curso.pregunta', 'curso_id', string='Preguntas del examen')
    total_preguntas = fields.Integer(
        string='No. de preguntas', compute='_compute_total_preguntas', store=True)

    intento_ids = fields.One2many(
        'amunet.curso.intento', 'curso_id', string='Intentos')
    intento_count = fields.Integer(
        string='Intentos realizados', compute='_compute_intento_count')

    equipment_ids = fields.Many2many(
        'amunet.equipment', string='Equipos relacionados',
        compute='_compute_equipment_ids',
        help='Maquinas/equipos que requieren este curso (derivado de los PNOs).')
    equipment_count = fields.Integer(
        string='Equipos', compute='_compute_equipment_ids')

    mi_estado = fields.Selection([
        ('sin_iniciar', 'Sin iniciar'),
        ('vigente', 'Vigente'),
        ('por_vencer', 'Por vencer'),
        ('vencida', 'Vencida'),
    ], string='Mi estado', compute='_compute_mi_estado',
        search='_search_mi_estado')
    mi_intento_count = fields.Integer(
        string='Mis intentos', compute='_compute_mi_estado')

    mi_estudio_inicio = fields.Datetime(
        string='Inicie el estudio', compute='_compute_mi_estudio')
    mi_puede_examinar = fields.Boolean(
        string='Puedo presentar el examen', compute='_compute_mi_estudio')
    mi_estudio_mensaje = fields.Char(
        string='Aviso de estudio', compute='_compute_mi_estudio')

    @api.depends('video_ids')
    def _compute_video_count(self):
        for curso in self:
            curso.video_count = len(curso.video_ids)

    @api.depends('pregunta_ids')
    def _compute_total_preguntas(self):
        for curso in self:
            curso.total_preguntas = len(curso.pregunta_ids)

    @api.depends('intento_ids')
    def _compute_intento_count(self):
        for curso in self:
            curso.intento_count = len(curso.intento_ids)

    @api.depends('procedure_ids')
    def _compute_equipment_ids(self):
        Equipment = self.env['amunet.equipment']
        for curso in self:
            if curso.procedure_ids:
                equipos = Equipment.search(
                    [('procedure_ids', 'in', curso.procedure_ids.ids)])
            else:
                equipos = Equipment.browse()
            curso.equipment_ids = equipos
            curso.equipment_count = len(equipos)

    @api.depends_context('uid')
    def _compute_mi_estado(self):
        Registro = self.env['amunet.registro.capacitacion'].sudo()
        Intento = self.env['amunet.curso.intento'].sudo()
        uid = self.env.uid
        for curso in self:
            curso.mi_intento_count = Intento.search_count([
                ('curso_id', '=', curso.id), ('user_id', '=', uid)])
            estado = 'sin_iniciar'
            if curso.procedure_ids:
                regs = Registro.search([
                    ('user_id', '=', uid),
                    ('procedure_id', 'in', curso.procedure_ids.ids),
                    ('state', '!=', 'cancelada'),
                ])
                if regs:
                    requeridos = set(curso.procedure_ids.ids)
                    vigentes = set(regs.filtered(
                        lambda r: r.state == 'vigente').mapped('procedure_id').ids)
                    proximos = set(regs.filtered(
                        lambda r: r.state == 'proxima').mapped('procedure_id').ids)
                    if requeridos <= vigentes:
                        estado = 'vigente'
                    elif requeridos <= (vigentes | proximos):
                        estado = 'por_vencer'
                    else:
                        estado = 'vencida'
            else:
                domain = [
                    ('curso_id', '=', curso.id), ('user_id', '=', uid),
                    ('state', '=', 'terminado'), ('aprobado', '=', True),
                ]
                if curso.validez_meses > 0:
                    vigente_desde = fields.Datetime.to_datetime(
                        fields.Date.today()
                        - relativedelta(months=curso.validez_meses))
                    domain.append(('fecha_fin', '>=', vigente_desde))
                aprob = Intento.search_count(domain)
                estado = 'vigente' if aprob else 'sin_iniciar'
            curso.mi_estado = estado

    @api.depends_context('uid')
    def _compute_mi_estudio(self):
        Estudio = self.env['amunet.curso.estudio'].sudo()
        uid = self.env.uid
        now = fields.Datetime.now()
        for curso in self:
            estudio = Estudio.search([
                ('curso_id', '=', curso.id), ('user_id', '=', uid)], limit=1)
            curso.mi_estudio_inicio = estudio.fecha_inicio if estudio else False
            minimo = curso.tiempo_minimo_estudio or 0
            if minimo <= 0:
                curso.mi_puede_examinar = True
                curso.mi_estudio_mensaje = False
            elif not estudio:
                curso.mi_puede_examinar = False
                curso.mi_estudio_mensaje = (
                    'Pulsa "Comenzar el curso" y dedica al menos %d minuto(s) '
                    'al contenido antes de presentar el examen.' % minimo)
            else:
                transcurrido = (now - estudio.fecha_inicio).total_seconds() / 60.0
                if transcurrido >= minimo:
                    curso.mi_puede_examinar = True
                    curso.mi_estudio_mensaje = False
                else:
                    faltan = int(minimo - transcurrido) + 1
                    curso.mi_puede_examinar = False
                    curso.mi_estudio_mensaje = (
                        'Sigue revisando el contenido. Podras presentar el '
                        'examen en aproximadamente %d minuto(s).' % faltan)

    def _search_mi_estado(self, operator, value):
        """Permite filtrar "Mis Cursos" por el estado del usuario actual."""
        cursos = self.search([('state', '=', 'publicado')])
        if operator == '=':
            ids = cursos.filtered(lambda c: c.mi_estado == value).ids
        elif operator == '!=':
            ids = cursos.filtered(lambda c: c.mi_estado != value).ids
        elif operator == 'in':
            ids = cursos.filtered(lambda c: c.mi_estado in value).ids
        elif operator == 'not in':
            ids = cursos.filtered(lambda c: c.mi_estado not in value).ids
        else:
            ids = cursos.ids
        return [('id', 'in', ids)]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'Nuevo') == 'Nuevo':
                vals['code'] = (
                    self.env['ir.sequence'].next_by_code('amunet.curso')
                    or 'CURSO-000')
        return super().create(vals_list)

    @api.constrains('calificacion_minima')
    def _check_calificacion_minima(self):
        for curso in self:
            if not (0 < curso.calificacion_minima <= 100):
                raise ValidationError(
                    "La calificacion minima debe estar entre 1 y 100.")

    @api.constrains('validez_meses', 'tiempo_minimo_estudio', 'tiempo_limite_examen')
    def _check_tiempos(self):
        for curso in self:
            if curso.validez_meses < 0:
                raise ValidationError(
                    "La vigencia en meses no puede ser negativa.")
            if curso.tiempo_minimo_estudio < 0:
                raise ValidationError(
                    "El tiempo minimo de estudio no puede ser negativo.")
            if curso.tiempo_limite_examen < 0:
                raise ValidationError(
                    "El tiempo limite del examen no puede ser negativo.")

    def action_publicar(self):
        for curso in self:
            if not curso.pregunta_ids:
                raise UserError(
                    "No se puede publicar el curso '%s': no tiene preguntas "
                    "de examen." % curso.name)
            for preg in curso.pregunta_ids:
                if not preg.respuesta_ids:
                    raise UserError(
                        "La pregunta '%s' no tiene respuestas." % (preg.texto or ''))
                if not any(r.es_correcta for r in preg.respuesta_ids):
                    raise UserError(
                        "La pregunta '%s' no tiene ninguna respuesta marcada "
                        "como correcta." % (preg.texto or ''))
            curso.state = 'publicado'

    def action_volver_borrador(self):
        self.write({'state': 'borrador'})

    def action_marcar_revisado(self):
        """Libera la marca de revision tras revisar el curso."""
        for curso in self:
            curso.revision_requerida = False
            curso.revision_motivo = False
            curso.message_post(body='Revision del curso liberada por %s.'
                               % self.env.user.name)

    def action_comenzar_estudio(self):
        """Registra el inicio de estudio del usuario actual para este curso."""
        self.ensure_one()
        if self.state != 'publicado':
            raise UserError("Este curso aun no esta publicado.")
        Estudio = self.env['amunet.curso.estudio']
        estudio = Estudio.search([
            ('curso_id', '=', self.id), ('user_id', '=', self.env.uid)], limit=1)
        if not estudio:
            Estudio.with_context(amunet_study_start=True).create({
                'curso_id': self.id,
                'user_id': self.env.uid,
            })
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def _check_user_can_start_exam(self, user):
        self.ensure_one()
        if self.state != 'publicado':
            raise UserError("Este curso aun no esta publicado.")
        if not self.pregunta_ids:
            raise UserError("Este curso no tiene examen configurado.")
        # Control de tiempo minimo de estudio
        if self.tiempo_minimo_estudio > 0:
            Estudio = self.env['amunet.curso.estudio'].sudo()
            estudio = Estudio.search([
                ('curso_id', '=', self.id),
                ('user_id', '=', user.id)], limit=1)
            if not estudio:
                raise UserError(
                    "Antes de presentar el examen debes pulsar 'Comenzar el "
                    "curso' y dedicar al menos %d minuto(s) al contenido."
                    % self.tiempo_minimo_estudio)
            transcurrido = (fields.Datetime.now() - estudio.fecha_inicio
                            ).total_seconds() / 60.0
            if transcurrido < self.tiempo_minimo_estudio:
                faltan = int(self.tiempo_minimo_estudio - transcurrido) + 1
                raise UserError(
                    "Aun no puedes presentar el examen. Debes dedicar al menos "
                    "%d minuto(s) al contenido; faltan aproximadamente %d "
                    "minuto(s)." % (self.tiempo_minimo_estudio, faltan))
        return True

    def action_iniciar_examen(self):
        self.ensure_one()
        self._check_user_can_start_exam(self.env.user)
        intento = self.env['amunet.curso.intento'].with_context(
            amunet_exam_start=True).create({
            'curso_id': self.id,
            'user_id': self.env.uid,
            'linea_ids': [(0, 0, {'pregunta_id': p.id})
                          for p in self.pregunta_ids],
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Examen: %s' % self.name,
            'res_model': 'amunet.curso.intento',
            'res_id': intento.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_equipos(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Equipos que requieren %s' % self.name,
            'res_model': 'amunet.equipment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.equipment_ids.ids)],
        }

    def action_view_intentos(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Intentos: %s' % self.name,
            'res_model': 'amunet.curso.intento',
            'view_mode': 'list,form',
            'domain': [('curso_id', '=', self.id)],
            'context': {'default_curso_id': self.id},
        }
