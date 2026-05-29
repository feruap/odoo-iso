# -*- coding: utf-8 -*-
from odoo import models, fields


class HrTrainingEvidence(models.Model):
    """Evidencia documental de capacitación ligada a un empleado.

    Registro regulatorio ISO 13485 §6.2 — no se borra, solo RH puede editar.
    """
    _name = 'hr.training.evidence'
    _description = 'Evidencia de Capacitación por Empleado'
    _order = 'date desc, id desc'

    employee_id = fields.Many2one(
        'hr.employee', string='Empleado',
        required=True, ondelete='restrict', index=True,
    )
    name = fields.Char(string='Descripción', required=True)
    document_type = fields.Selection([
        ('constancia', 'Constancia'),
        ('diploma', 'Diploma'),
        ('certificado', 'Certificado'),
        ('otro', 'Otro'),
    ], string='Tipo', default='constancia', required=True)
    date = fields.Date(string='Fecha del documento')
    course_id = fields.Many2one(
        'hr.training.course', string='Curso relacionado',
    )
    file = fields.Binary(string='Archivo', attachment=True)
    filename = fields.Char()
    notes = fields.Char(string='Observaciones')
