# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # groups= igual al de la pestana que los muestra (hr.group_hr_user).
    # Sin el, cualquier lectura de la ficha del empleado por un usuario fuera
    # de RRHH cae en hr.employee.public, donde estos campos no existen, y Odoo
    # corta con AccessError "no estan disponibles para los perfiles publicos".
    # No quita acceso a nadie: la pestana ya era solo de RRHH, y los cursos se
    # siguen leyendo por su propio menu (ACL base.group_user).
    training_attendance_ids = fields.One2many(
        'hr.training.attendance', 'employee_id',
        string='Historial de cursos',
        groups='hr.group_hr_user',
    )
    training_evidence_ids = fields.One2many(
        'hr.training.evidence', 'employee_id',
        string='Evidencias y certificados',
        groups='hr.group_hr_user',
    )
