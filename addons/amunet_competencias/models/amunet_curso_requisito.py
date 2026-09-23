# -*- coding: utf-8 -*-
from odoo import models, fields


class AmunetCursoRequisito(models.Model):
    _name = 'amunet.curso.requisito'
    _description = 'Curso requerido por área o empleados'
    _order = 'course_id'

    course_id = fields.Many2one(
        'hr.training.course', required=True, string='Curso', ondelete='cascade')
    aplica_todos = fields.Boolean(
        default=False, string='Aplica a todos',
        help='Si está marcado, aplica a todos los empleados activos excepto los departamentos excluidos.')
    department_ids = fields.Many2many(
        'hr.department',
        'amunet_req_dept_rel', 'requisito_id', 'department_id',
        string='Departamentos')
    excluir_department_ids = fields.Many2many(
        'hr.department',
        'amunet_req_excl_dept_rel', 'requisito_id', 'department_id',
        string='Departamentos excluidos')
    employee_ids = fields.Many2many(
        'hr.employee',
        'amunet_req_emp_rel', 'requisito_id', 'employee_id',
        string='Empleados específicos')
