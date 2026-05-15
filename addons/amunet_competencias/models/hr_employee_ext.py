# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrEmployee(models.Model):
    """
    Extension del empleado: avance de capacitacion segun los planes
    de estudio que aplican a su puesto o departamento.
    """
    _inherit = 'hr.employee'

    amunet_plan_ids = fields.Many2many(
        'amunet.plan.estudios', string='Planes de estudio aplicables',
        compute='_compute_amunet_avance')
    amunet_cursos_requeridos = fields.Integer(
        string='Cursos requeridos', compute='_compute_amunet_avance')
    amunet_cursos_vigentes = fields.Integer(
        string='Cursos al corriente', compute='_compute_amunet_avance')
    amunet_cursos_pendientes = fields.Integer(
        string='Cursos pendientes', compute='_compute_amunet_avance')
    amunet_avance = fields.Float(
        string='Avance de capacitacion (%)', compute='_compute_amunet_avance',
        help='Porcentaje de cursos del plan de estudios que el empleado '
             'tiene con capacitacion vigente.')

    @api.depends('job_id', 'department_id', 'user_id')
    def _compute_amunet_avance(self):
        Plan = self.env['amunet.plan.estudios'].sudo()
        Registro = self.env['amunet.registro.capacitacion'].sudo()
        for emp in self:
            planes = Plan.browse()
            if emp.job_id or emp.department_id:
                domain = []
                if emp.job_id:
                    domain.append(('job_ids', 'in', emp.job_id.id))
                if emp.department_id:
                    domain.append(('department_ids', 'in', emp.department_id.id))
                if len(domain) == 2:
                    domain = ['|'] + domain
                planes = Plan.search(domain)

            cursos = planes.mapped('linea_ids').filtered('obligatorio').mapped('curso_id')
            total = len(cursos)
            vigentes = 0
            if emp.user_id and cursos:
                regs = Registro.search([
                    ('user_id', '=', emp.user_id.id),
                    ('state', '=', 'vigente'),
                ])
                procs_vigentes = set(regs.mapped('procedure_id').ids)
                for curso in cursos:
                    if curso.procedure_ids and (set(curso.procedure_ids.ids) & procs_vigentes):
                        vigentes += 1

            emp.amunet_plan_ids = planes
            emp.amunet_cursos_requeridos = total
            emp.amunet_cursos_vigentes = vigentes
            emp.amunet_cursos_pendientes = total - vigentes
            emp.amunet_avance = (vigentes / total * 100.0) if total else 0.0
