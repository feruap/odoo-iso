# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AmunetEquipmentCurso(models.Model):
    """
    Extension del equipo: lista los cursos de capacitacion que requiere,
    derivados automaticamente de los PNOs asignados al equipo.
    El PNO es el puente entre el area de cursos y el area de maquinas.
    """
    _inherit = 'amunet.equipment'

    curso_ids = fields.Many2many(
        'amunet.curso', string='Cursos de capacitacion',
        compute='_compute_curso_ids',
        help='Cursos que un operador debe aprobar para quedar capacitado en '
             'este equipo. Se derivan automaticamente de los PNOs del equipo.')
    curso_count = fields.Integer(
        string='Cursos', compute='_compute_curso_ids')

    @api.depends('procedure_ids')
    def _compute_curso_ids(self):
        Curso = self.env['amunet.curso']
        for eq in self:
            if eq.procedure_ids:
                cursos = Curso.search(
                    [('procedure_ids', 'in', eq.procedure_ids.ids)])
            else:
                cursos = Curso.browse()
            eq.curso_ids = cursos
            eq.curso_count = len(cursos)
