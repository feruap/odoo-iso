# -*- coding: utf-8 -*-
import logging
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AmunetCursoIntento(models.Model):
    """
    Intento / examen presentado por un usuario sobre un curso.
    Guarda las respuestas, calcula la calificacion y, si aprueba,
    genera automaticamente los registros de capacitacion.

    ISO 13485:2016 6.2 - registro auditable de la evaluacion.
    """
    _name = 'amunet.curso.intento'
    _description = 'Intento de Examen de Curso (ISO 13485 6.2)'
    _inherit = ['mail.thread']
    _order = 'create_date desc, id desc'

    name = fields.Char(
        string='Referencia', readonly=True, copy=False, default='Nuevo')
    curso_id = fields.Many2one(
        'amunet.curso', string='Curso', required=True,
        ondelete='restrict', tracking=True)
    user_id = fields.Many2one(
        'res.users', string='Usuario', required=True,
        default=lambda self: self.env.uid, tracking=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Empleado',
        compute='_compute_employee_id', store=True)

    fecha_inicio = fields.Datetime(
        string='Inicio', default=fields.Datetime.now, readonly=True)
    fecha_fin = fields.Datetime(string='Fin', readonly=True)

    state = fields.Selection([
        ('en_progreso', 'En progreso'),
        ('terminado', 'Terminado'),
    ], string='Estado', default='en_progreso', required=True, tracking=True)

    linea_ids = fields.One2many(
        'amunet.curso.intento.linea', 'intento_id', string='Respuestas')

    calificacion = fields.Float(
        string='Calificacion (%)', compute='_compute_calificacion',
        store=True, tracking=True)
    aprobado = fields.Boolean(
        string='Aprobado', compute='_compute_calificacion',
        store=True, tracking=True)
    calificacion_minima = fields.Float(
        related='curso_id.calificacion_minima',
        string='Minima para aprobar (%)')

    descripcion = fields.Html(
        related='curso_id.descripcion', string='Contenido del curso')
    video_url = fields.Char(related='curso_id.video_url', string='Video')
    material_ids = fields.Many2many(
        related='curso_id.material_ids', string='Material de apoyo')

    registro_ids = fields.One2many(
        'amunet.registro.capacitacion', 'intento_id',
        string='Registros generados')
    registro_count = fields.Integer(compute='_compute_registro_count')

    @api.depends('user_id')
    def _compute_employee_id(self):
        for rec in self:
            rec.employee_id = self.env['hr.employee'].sudo().search(
                [('user_id', '=', rec.user_id.id)], limit=1)

    @api.depends('linea_ids.es_correcta', 'linea_ids.puntos',
                 'curso_id.calificacion_minima')
    def _compute_calificacion(self):
        for intento in self:
            total = sum(intento.linea_ids.mapped('puntos'))
            obtenidos = sum(
                l.puntos for l in intento.linea_ids if l.es_correcta)
            intento.calificacion = (
                obtenidos / total * 100.0) if total else 0.0
            intento.aprobado = (
                total > 0
                and intento.calificacion >= intento.curso_id.calificacion_minima)

    def _compute_registro_count(self):
        for rec in self:
            rec.registro_count = len(rec.registro_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = (
                    self.env['ir.sequence'].sudo().next_by_code(
                        'amunet.curso.intento') or 'INT-000')
        return super().create(vals_list)

    def action_finalizar(self):
        self.ensure_one()
        if self.state == 'terminado':
            raise UserError("Este examen ya fue finalizado.")
        sin_responder = self.linea_ids.filtered(lambda l: not l.respuesta_id)
        if sin_responder:
            raise UserError(
                "Debe responder todas las preguntas antes de finalizar "
                "(faltan %d)." % len(sin_responder))
        self.write({
            'state': 'terminado',
            'fecha_fin': fields.Datetime.now(),
        })
        self.invalidate_recordset(['calificacion', 'aprobado'])
        if self.aprobado:
            self._generar_registros()
            msg = "Examen aprobado con %.1f%%." % self.calificacion
        else:
            msg = ("Examen no aprobado (%.1f%%, minimo %.1f%%)."
                   % (self.calificacion, self.curso_id.calificacion_minima))
        self.message_post(body=msg)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'amunet.curso.intento',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _generar_registros(self):
        """Crea un registro de capacitacion vigente por cada PNO del curso."""
        self.ensure_one()
        Registro = self.env['amunet.registro.capacitacion'].sudo()
        curso = self.curso_id.sudo()
        hoy = fields.Date.context_today(self)
        if curso.validez_meses > 0:
            expiry = hoy + relativedelta(months=curso.validez_meses)
        else:
            expiry = hoy + relativedelta(years=100)
        for proc in curso.procedure_ids:
            Registro.create({
                'user_id': self.user_id.id,
                'procedure_id': proc.id,
                'training_date': hoy,
                'expiry_date': expiry,
                'training_type': 'virtual',
                'trainer_id': False,
                'intento_id': self.id,
                'notes': ('Generado automaticamente al aprobar el curso "%s" '
                          '(intento %s, calificacion %.1f%%).'
                          % (curso.name, self.name, self.calificacion)),
            })

    def action_view_registros(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Registros generados',
            'res_model': 'amunet.registro.capacitacion',
            'view_mode': 'list,form',
            'domain': [('intento_id', '=', self.id)],
        }


class AmunetCursoIntentoLinea(models.Model):
    """Respuesta del usuario a una pregunta dentro de un intento."""
    _name = 'amunet.curso.intento.linea'
    _description = 'Respuesta de un Intento de Examen'
    _order = 'intento_id, pregunta_secuencia, id'

    intento_id = fields.Many2one(
        'amunet.curso.intento', string='Intento', required=True,
        ondelete='cascade')
    pregunta_id = fields.Many2one(
        'amunet.curso.pregunta', string='Pregunta (ref)', required=True,
        ondelete='restrict')
    pregunta_secuencia = fields.Integer(
        related='pregunta_id.secuencia', store=True)
    pregunta_texto = fields.Text(
        related='pregunta_id.texto', string='Pregunta')
    puntos = fields.Integer(
        related='pregunta_id.puntos', string='Puntos', store=True)
    respuesta_id = fields.Many2one(
        'amunet.curso.respuesta', string='Tu respuesta',
        domain="[('pregunta_id', '=', pregunta_id)]")
    es_correcta = fields.Boolean(
        string='Correcta', compute='_compute_es_correcta', store=True)

    @api.depends('respuesta_id', 'respuesta_id.es_correcta')
    def _compute_es_correcta(self):
        for linea in self:
            linea.es_correcta = bool(
                linea.respuesta_id and linea.respuesta_id.es_correcta)
