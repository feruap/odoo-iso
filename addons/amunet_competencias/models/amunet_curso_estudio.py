# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AmunetCursoEstudio(models.Model):
    """
    Registra cuando un usuario comienza a estudiar un curso.
    Sirve para hacer cumplir el tiempo minimo de estudio antes de
    habilitar el examen.
    """
    _name = 'amunet.curso.estudio'
    _description = 'Sesion de Estudio de un Curso'
    _order = 'create_date desc, id desc'

    curso_id = fields.Many2one(
        'amunet.curso', string='Curso', required=True, ondelete='cascade')
    user_id = fields.Many2one(
        'res.users', string='Usuario', required=True,
        default=lambda self: self.env.uid)
    fecha_inicio = fields.Datetime(
        string='Inicio del estudio', default=fields.Datetime.now, readonly=True)
