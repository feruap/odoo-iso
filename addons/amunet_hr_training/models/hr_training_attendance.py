# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrTrainingAttendance(models.Model):
    """Pase de lista por empleado en una capacitacion.

    Una linea por (curso, empleado) que registra si asistio, si llego
    a tiempo y la calificacion final obtenida.
    """
    _name = 'hr.training.attendance'
    _description = 'Asistencia y calificacion - Capacitacion'
    _order = 'course_id, employee_id'

    course_id = fields.Many2one(
        'hr.training.course',
        string='Capacitacion',
        required=True, ondelete='cascade', index=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Participante',
        required=True, index=True,
    )

    attendance = fields.Selection(
        [
            ('attended', 'Asistio'),
            ('absent', 'Falto'),
        ],
        string='Asistencia', default='attended', required=True,
    )
    on_time = fields.Boolean(
        string='Llego a tiempo', default=True,
        help='Marcado si el participante se presento puntual.',
    )
    grade = fields.Float(
        string='Calificacion', digits=(5, 2),
        help='Calificacion final obtenida (0 a 100, o el rango que '
             'corresponda a la capacitacion).',
    )
    notes = fields.Char(string='Observaciones')

    # Estado del curso (related para facilitar filtros en la vista)
    course_state = fields.Selection(
        related='course_id.state', store=True, string='Estado del curso')

    _sql_constraints = [
        ('uniq_course_employee',
         'unique(course_id, employee_id)',
         'No se puede agregar dos veces el mismo empleado a un curso.'),
    ]

    @api.constrains('grade')
    def _check_grade(self):
        for rec in self:
            if rec.grade < 0 or rec.grade > 100:
                raise ValidationError(_(
                    'La calificacion debe estar entre 0 y 100.'))
