# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError


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

    def _is_competencias_manager(self):
        return self.env.user.has_group(
            'amunet_competencias.group_competencias_manager')

    @api.model_create_multi
    def create(self, vals_list):
        if not self._is_competencias_manager():
            if not self.env.context.get('amunet_study_start'):
                raise AccessError(
                    "Las sesiones de estudio solo pueden iniciarse desde "
                    "el boton 'Comenzar el curso'.")
            for vals in vals_list:
                curso = self.env['amunet.curso'].browse(
                    vals.get('curso_id')).exists()
                if not curso:
                    raise UserError("Debe indicar un curso valido.")
                if curso.state != 'publicado':
                    raise UserError("Este curso aun no esta publicado.")
                vals['user_id'] = self.env.uid
                vals.pop('fecha_inicio', None)
        return super().create(vals_list)

    def write(self, vals):
        if not self._is_competencias_manager():
            raise AccessError(
                "La fecha de inicio de estudio no puede modificarse manualmente.")
        return super().write(vals)

    def unlink(self):
        if not self._is_competencias_manager():
            raise AccessError(
                "Las sesiones de estudio no pueden eliminarse manualmente.")
        return super().unlink()
