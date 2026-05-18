# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError

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
    fecha_limite = fields.Datetime(
        string='Fecha limite', compute='_compute_fecha_limite',
        help='Hora maxima para finalizar el examen, segun el tiempo limite '
             'del curso.')

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

    tiempo_limite_examen = fields.Integer(
        related='curso_id.tiempo_limite_examen',
        string='Tiempo limite (min)')
    fuera_de_tiempo = fields.Boolean(
        string='Finalizado fuera de tiempo', default=False, readonly=True,
        help='El examen se finalizo despues del tiempo limite. En ese caso '
             'no se considera aprobado aunque la calificacion sea suficiente.')

    descripcion = fields.Html(
        related='curso_id.descripcion', string='Contenido del curso')
    video_ids = fields.One2many(
        related='curso_id.video_ids', string='Videos del curso')
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

    @api.depends('fecha_inicio', 'tiempo_limite_examen')
    def _compute_fecha_limite(self):
        for rec in self:
            if rec.fecha_inicio and rec.tiempo_limite_examen > 0:
                rec.fecha_limite = rec.fecha_inicio + timedelta(
                    minutes=rec.tiempo_limite_examen)
            else:
                rec.fecha_limite = False

    @api.depends('linea_ids.es_correcta', 'linea_ids.puntos',
                 'curso_id.calificacion_minima', 'fuera_de_tiempo')
    def _compute_calificacion(self):
        for intento in self:
            total = sum(intento.linea_ids.mapped('puntos'))
            obtenidos = sum(
                l.puntos for l in intento.linea_ids if l.es_correcta)
            intento.calificacion = (
                obtenidos / total * 100.0) if total else 0.0
            intento.aprobado = (
                total > 0
                and intento.calificacion >= intento.curso_id.calificacion_minima
                and not intento.fuera_de_tiempo)

    def _compute_registro_count(self):
        for rec in self:
            rec.registro_count = len(rec.registro_ids)

    def _is_competencias_manager(self):
        return self.env.user.has_group(
            'amunet_competencias.group_competencias_manager')

    def _check_owner_or_manager(self):
        if self._is_competencias_manager():
            return True
        ajenos = self.filtered(lambda r: r.user_id.id != self.env.uid)
        if ajenos:
            raise AccessError("Solo puedes operar tus propios examenes.")
        return True

    @api.model_create_multi
    def create(self, vals_list):
        is_manager = self.env.user.has_group(
            'amunet_competencias.group_competencias_manager')
        if not is_manager:
            if not self.env.context.get('amunet_exam_start'):
                raise AccessError(
                    "Los intentos de examen solo pueden crearse desde "
                    "el boton oficial del curso.")
            forbidden = {
                'fecha_fin', 'fuera_de_tiempo', 'calificacion',
                'aprobado', 'registro_ids', 'employee_id',
            }
            for vals in vals_list:
                if forbidden.intersection(vals):
                    raise AccessError(
                        "No puedes predefinir el resultado de un examen.")
                if vals.get('state') not in (None, 'en_progreso'):
                    raise AccessError(
                        "Un examen nuevo siempre debe iniciar en progreso.")
                curso = self.env['amunet.curso'].browse(
                    vals.get('curso_id')).exists()
                if not curso:
                    raise UserError("Debe indicar un curso valido.")
                curso._check_user_can_start_exam(self.env.user)
                vals['user_id'] = self.env.uid
                vals['state'] = 'en_progreso'
                vals.pop('fecha_inicio', None)
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = (
                    self.env['ir.sequence'].sudo().next_by_code(
                        'amunet.curso.intento') or 'INT-000')
        return super().create(vals_list)

    def write(self, vals):
        if not self._is_competencias_manager():
            self._check_owner_or_manager()
            if any(rec.state == 'terminado' for rec in self):
                raise AccessError("Un examen finalizado no puede modificarse.")
            if self.env.context.get('amunet_exam_finalize'):
                allowed = {'state', 'fecha_fin', 'fuera_de_tiempo'}
                if set(vals) - allowed or vals.get('state') != 'terminado':
                    raise AccessError(
                        "El cierre de examen solo puede guardar el resultado final.")
            else:
                allowed = {'linea_ids'}
                if set(vals) - allowed:
                    raise AccessError(
                        "Solo puedes responder preguntas del examen en progreso.")
        return super().write(vals)

    def action_finalizar(self):
        self.ensure_one()
        self._check_owner_or_manager()
        if self.state == 'terminado':
            raise UserError("Este examen ya fue finalizado.")
        if self.curso_id.state != 'publicado':
            raise UserError("Este curso ya no esta publicado.")
        if not self._is_competencias_manager():
            self.curso_id._check_user_can_start_exam(self.env.user)
        self._check_line_integrity()
        sin_responder = self.linea_ids.filtered(lambda l: not l.respuesta_id)
        if sin_responder:
            raise UserError(
                "Debe responder todas las preguntas antes de finalizar "
                "(faltan %d)." % len(sin_responder))
        ahora = fields.Datetime.now()
        # Control de tiempo limite del examen
        fuera = False
        if self.tiempo_limite_examen > 0 and self.fecha_inicio:
            limite = self.fecha_inicio + timedelta(minutes=self.tiempo_limite_examen)
            if ahora > limite:
                fuera = True
        self.with_context(amunet_exam_finalize=True).write({
            'state': 'terminado',
            'fecha_fin': ahora,
            'fuera_de_tiempo': fuera,
        })
        self.invalidate_recordset(['calificacion', 'aprobado'])
        if self.aprobado:
            self._generar_registros()
            msg = "Examen aprobado con %.1f%%." % self.calificacion
        elif fuera:
            msg = ("Examen finalizado FUERA DE TIEMPO (%.1f%%). No se considera "
                   "aprobado. Debe repetirse dentro del tiempo limite."
                   % self.calificacion)
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

    def _check_line_integrity(self):
        self.ensure_one()
        preguntas = self.curso_id.pregunta_ids
        expected = set(preguntas.ids)
        actual = self.linea_ids.mapped('pregunta_id')
        if len(actual) != len(self.linea_ids) or set(actual.ids) != expected:
            raise UserError(
                "Las preguntas del examen no coinciden con el curso publicado.")
        for linea in self.linea_ids:
            if linea.pregunta_id.curso_id != self.curso_id:
                raise UserError(
                    "Una pregunta del intento no pertenece a este curso.")
            if (linea.respuesta_id
                    and linea.respuesta_id.pregunta_id != linea.pregunta_id):
                raise UserError(
                    "Una respuesta seleccionada no corresponde a su pregunta.")
        return True

    def _generar_registros(self):
        """Crea un registro de capacitacion vigente por cada PNO del curso."""
        self.ensure_one()
        if self.state != 'terminado' or not self.aprobado:
            raise UserError(
                "Solo un examen terminado y aprobado puede generar registros.")
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
        string='Correcta', compute='_compute_es_correcta', store=True,
        groups='amunet_competencias.group_competencias_manager')

    @api.depends('respuesta_id', 'respuesta_id.es_correcta')
    def _compute_es_correcta(self):
        for linea in self:
            linea.es_correcta = bool(
                linea.respuesta_id and linea.respuesta_id.es_correcta)

    def _is_competencias_manager(self):
        return self.env.user.has_group(
            'amunet_competencias.group_competencias_manager')

    def _check_editable_by_user(self):
        if self._is_competencias_manager():
            return True
        ajenas = self.filtered(lambda l: l.intento_id.user_id.id != self.env.uid)
        if ajenas:
            raise AccessError("Solo puedes responder tus propios examenes.")
        cerradas = self.filtered(lambda l: l.intento_id.state != 'en_progreso')
        if cerradas:
            raise AccessError("No puedes modificar un examen finalizado.")
        return True

    @api.model_create_multi
    def create(self, vals_list):
        if not self._is_competencias_manager():
            if not self.env.context.get('amunet_exam_start'):
                raise AccessError(
                    "Las preguntas del intento solo pueden generarse al "
                    "iniciar el examen desde el curso.")
            for vals in vals_list:
                if vals.get('respuesta_id'):
                    raise AccessError(
                        "Un examen nuevo no puede nacer con respuestas.")
                intento = self.env['amunet.curso.intento'].browse(
                    vals.get('intento_id')).exists()
                pregunta = self.env['amunet.curso.pregunta'].browse(
                    vals.get('pregunta_id')).exists()
                if not intento or intento.user_id.id != self.env.uid:
                    raise AccessError(
                        "Solo puedes crear lineas para tu propio examen.")
                if not pregunta or pregunta.curso_id != intento.curso_id:
                    raise UserError(
                        "La pregunta no pertenece al curso del examen.")
        return super().create(vals_list)

    def write(self, vals):
        if not self._is_competencias_manager():
            self._check_editable_by_user()
            if set(vals) - {'respuesta_id'}:
                raise AccessError(
                    "Solo puedes cambiar tu respuesta seleccionada.")
            respuesta_id = vals.get('respuesta_id')
            if respuesta_id:
                respuesta = self.env['amunet.curso.respuesta'].browse(
                    respuesta_id).exists()
                if not respuesta:
                    raise UserError("La respuesta seleccionada no existe.")
                for linea in self:
                    if respuesta.pregunta_id != linea.pregunta_id:
                        raise UserError(
                            "La respuesta seleccionada no corresponde a la pregunta.")
        return super().write(vals)

    def unlink(self):
        if not self._is_competencias_manager():
            raise AccessError("No puedes eliminar preguntas de un examen.")
        return super().unlink()
