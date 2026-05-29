# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    training_attendance_ids = fields.One2many(
        'hr.training.attendance', 'employee_id',
        string='Historial de cursos',
    )
    training_evidence_ids = fields.One2many(
        'hr.training.evidence', 'employee_id',
        string='Evidencias y certificados',
    )
