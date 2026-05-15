# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AmunetPlanEstudios(models.Model):
    """
    Plan de estudios / curricula de capacitacion.
    Define que cursos debe llevar cada puesto o departamento.
    ISO 13485:2016 6.2 - determinacion de la competencia necesaria.
    """
    _name = 'amunet.plan.estudios'
    _description = 'Plan de Estudios de Capacitacion (ISO 13485 6.2)'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(string='Nombre del plan', required=True, tracking=True)
    code = fields.Char(string='Codigo', readonly=True, copy=False, default='Nuevo')
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Descripcion / Notas')

    job_ids = fields.Many2many(
        'hr.job', 'amunet_plan_job_rel', 'plan_id', 'job_id',
        string='Puestos', help='Puestos a los que aplica este plan de estudios.')
    department_ids = fields.Many2many(
        'hr.department', 'amunet_plan_department_rel', 'plan_id', 'department_id',
        string='Departamentos',
        help='Departamentos a los que aplica este plan de estudios.')

    linea_ids = fields.One2many(
        'amunet.plan.estudios.linea', 'plan_id', string='Cursos del plan')
    curso_count = fields.Integer(
        string='Cursos', compute='_compute_counts')
    empleado_count = fields.Integer(
        string='Empleados cubiertos', compute='_compute_counts')

    @api.depends('linea_ids', 'job_ids', 'department_ids')
    def _compute_counts(self):
        for plan in self:
            plan.curso_count = len(plan.linea_ids)
            plan.empleado_count = len(plan._empleados_cubiertos())

    def _empleados_cubiertos(self):
        """Empleados cuyo puesto o departamento coincide con el plan."""
        self.ensure_one()
        Employee = self.env['hr.employee'].sudo()
        domain = []
        if self.job_ids:
            domain.append(('job_id', 'in', self.job_ids.ids))
        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))
        if not domain:
            return Employee.browse()
        if len(domain) == 2:
            domain = ['|'] + domain
        return Employee.search(domain)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'Nuevo') == 'Nuevo':
                vals['code'] = (
                    self.env['ir.sequence'].next_by_code('amunet.plan.estudios')
                    or 'PLAN-000')
        return super().create(vals_list)

    def action_view_empleados(self):
        self.ensure_one()
        empleados = self._empleados_cubiertos()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Empleados del plan %s' % self.name,
            'res_model': 'hr.employee',
            'view_mode': 'list,form',
            'domain': [('id', 'in', empleados.ids)],
        }

    def action_view_avance(self):
        """Abre el tablero de avance filtrado a los empleados de este plan."""
        self.ensure_one()
        empleados = self._empleados_cubiertos()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Avance de capacitacion - %s' % self.name,
            'res_model': 'hr.employee',
            'view_mode': 'list,form',
            'domain': [('id', 'in', empleados.ids)],
            'context': {'search_default_group_department': 1},
        }


class AmunetPlanEstudiosLinea(models.Model):
    """Curso incluido en un plan de estudios."""
    _name = 'amunet.plan.estudios.linea'
    _description = 'Curso de un Plan de Estudios'
    _order = 'plan_id, secuencia, id'

    plan_id = fields.Many2one(
        'amunet.plan.estudios', string='Plan', required=True, ondelete='cascade')
    secuencia = fields.Integer(string='Orden', default=10)
    curso_id = fields.Many2one(
        'amunet.curso', string='Curso', required=True, ondelete='restrict')
    obligatorio = fields.Boolean(
        string='Obligatorio', default=True,
        help='Si esta marcado, el curso cuenta para el porcentaje de avance.')

    @api.constrains('plan_id', 'curso_id')
    def _check_curso_unico(self):
        for linea in self:
            dup = self.search_count([
                ('plan_id', '=', linea.plan_id.id),
                ('curso_id', '=', linea.curso_id.id),
                ('id', '!=', linea.id),
            ])
            if dup:
                raise ValidationError(
                    "El curso '%s' ya esta en este plan de estudios."
                    % (linea.curso_id.name or ''))
