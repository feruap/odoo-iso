# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class AmunetCurso(models.Model):
    """
    Curso de capacitacion. Reune en una sola ficha el contenido (video,
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

    video_url = fields.Char(
        string='Enlace de video',
        help='URL del video del curso (YouTube, Vimeo, enlace interno, etc.)')
    video_file = fields.Binary(string='Video (archivo)', attachment=True)
    video_filename = fields.Char(string='Nombre del archivo de video')

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
                    estados = regs.mapped('state')
                    if 'vigente' in estados:
                        estado = 'vigente'
                    elif 'proxima' in estados:
                        estado = 'por_vencer'
                    else:
                        estado = 'vencida'
            else:
                aprob = Intento.search_count([
                    ('curso_id', '=', curso.id), ('user_id', '=', uid),
                    ('state', '=', 'terminado'), ('aprobado', '=', True)])
                estado = 'vigente' if aprob else 'sin_iniciar'
            curso.mi_estado = estado

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

    @api.constrains('validez_meses')
    def _check_validez(self):
        for curso in self:
            if curso.validez_meses < 0:
                raise ValidationError(
                    "La vigencia en meses no puede ser negativa.")

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

    def action_iniciar_examen(self):
        self.ensure_one()
        if self.state != 'publicado':
            raise UserError("Este curso aun no esta publicado.")
        if not self.pregunta_ids:
            raise UserError("Este curso no tiene examen configurado.")
        intento = self.env['amunet.curso.intento'].create({
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
