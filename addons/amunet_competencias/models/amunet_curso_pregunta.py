# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AmunetCursoPregunta(models.Model):
    """Pregunta de opcion multiple del examen de un curso."""
    _name = 'amunet.curso.pregunta'
    _description = 'Pregunta de Examen de Curso'
    _order = 'curso_id, secuencia, id'

    curso_id = fields.Many2one(
        'amunet.curso', string='Curso', required=True, ondelete='cascade')
    secuencia = fields.Integer(string='Secuencia', default=10)
    texto = fields.Text(string='Pregunta', required=True)
    puntos = fields.Integer(
        string='Puntos', default=1, required=True,
        help='Peso de la pregunta en la calificacion final.')
    respuesta_ids = fields.One2many(
        'amunet.curso.respuesta', 'pregunta_id', string='Respuestas')

    @api.constrains('puntos')
    def _check_puntos(self):
        for p in self:
            if p.puntos < 1:
                raise ValidationError(
                    "Los puntos de una pregunta deben ser al menos 1.")

    @api.constrains('respuesta_ids')
    def _check_una_correcta(self):
        for p in self:
            if p.respuesta_ids and not any(
                    r.es_correcta for r in p.respuesta_ids):
                raise ValidationError(
                    "La pregunta '%s' debe tener al menos una respuesta "
                    "correcta." % (p.texto or ''))


class AmunetCursoRespuesta(models.Model):
    """Opcion de respuesta de una pregunta de examen."""
    _name = 'amunet.curso.respuesta'
    _description = 'Respuesta de Pregunta de Examen'
    _order = 'pregunta_id, id'

    pregunta_id = fields.Many2one(
        'amunet.curso.pregunta', string='Pregunta', required=True,
        ondelete='cascade')
    curso_id = fields.Many2one(
        related='pregunta_id.curso_id', store=True, string='Curso')
    texto = fields.Char(string='Respuesta', required=True)
    es_correcta = fields.Boolean(
        string='Es correcta',
        groups='amunet_competencias.group_competencias_manager')
