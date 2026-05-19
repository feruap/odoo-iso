# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
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
        string='Cursos requeridos', compute='_compute_amunet_avance',
        search='_search_amunet_cursos_requeridos')
    amunet_cursos_vigentes = fields.Integer(
        string='Cursos al corriente', compute='_compute_amunet_avance',
        search='_search_amunet_cursos_vigentes')
    amunet_cursos_pendientes = fields.Integer(
        string='Cursos pendientes', compute='_compute_amunet_avance',
        search='_search_amunet_cursos_pendientes')
    amunet_avance = fields.Float(
        string='Avance de capacitacion (%)', compute='_compute_amunet_avance',
        search='_search_amunet_avance',
        help='Porcentaje de cursos del plan de estudios que el empleado '
             'tiene con capacitacion vigente.')
    amunet_training_status = fields.Selection([
        ('no_plan', 'Sin plan'),
        ('complete', 'Completo'),
        ('gap', 'Con brecha'),
    ], string='Estado capacitacion', compute='_compute_amunet_avance')
    amunet_training_next_step = fields.Char(
        string='Siguiente paso',
        compute='_compute_amunet_avance')

    @api.depends('job_id', 'department_id', 'user_id')
    def _compute_amunet_avance(self):
        Plan = self.env['amunet.plan.estudios'].sudo()
        Registro = self.env['amunet.registro.capacitacion'].sudo()
        Intento = self.env['amunet.curso.intento'].sudo()
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
                    ('state', 'in', ('vigente', 'proxima')),
                ])
                procs_vigentes = set(regs.filtered(
                    lambda r: r.state == 'vigente').mapped('procedure_id').ids)
                procs_proximos = set(regs.filtered(
                    lambda r: r.state == 'proxima').mapped('procedure_id').ids)
                for curso in cursos:
                    requeridos = set(curso.procedure_ids.ids)
                    if requeridos and requeridos <= (procs_vigentes | procs_proximos):
                        vigentes += 1
                    elif not requeridos:
                        domain = [
                            ('curso_id', '=', curso.id),
                            ('user_id', '=', emp.user_id.id),
                            ('state', '=', 'terminado'),
                            ('aprobado', '=', True),
                        ]
                        if curso.validez_meses > 0:
                            vigente_desde = fields.Datetime.to_datetime(
                                fields.Date.today()
                                - relativedelta(months=curso.validez_meses))
                            domain.append(('fecha_fin', '>=', vigente_desde))
                        if Intento.search_count(domain):
                            vigentes += 1

            emp.amunet_plan_ids = planes
            emp.amunet_cursos_requeridos = total
            emp.amunet_cursos_vigentes = vigentes
            emp.amunet_cursos_pendientes = total - vigentes
            emp.amunet_avance = (vigentes / total * 100.0) if total else 0.0
            if not total:
                emp.amunet_training_status = 'no_plan'
                emp.amunet_training_next_step = 'Asignar plan de estudios'
            elif emp.amunet_cursos_pendientes:
                emp.amunet_training_status = 'gap'
                emp.amunet_training_next_step = 'Programar o completar cursos pendientes'
            else:
                emp.amunet_training_status = 'complete'
                emp.amunet_training_next_step = 'Sin accion inmediata'

    def _match_number(self, left, operator, right):
        if operator == '=':
            return left == right
        if operator == '!=':
            return left != right
        if operator == '>':
            return left > right
        if operator == '>=':
            return left >= right
        if operator == '<':
            return left < right
        if operator == '<=':
            return left <= right
        if operator == 'in':
            return left in right
        if operator == 'not in':
            return left not in right
        return False

    def _search_amunet_metric(self, field_name, operator, value):
        employees = self.sudo().search([])
        ids = employees.filtered(
            lambda emp: self._match_number(
                getattr(emp, field_name), operator, value)).ids
        return [('id', 'in', ids)]

    def _search_amunet_cursos_requeridos(self, operator, value):
        return self._search_amunet_metric(
            'amunet_cursos_requeridos', operator, value)

    def _search_amunet_cursos_vigentes(self, operator, value):
        return self._search_amunet_metric(
            'amunet_cursos_vigentes', operator, value)

    def _search_amunet_cursos_pendientes(self, operator, value):
        return self._search_amunet_metric(
            'amunet_cursos_pendientes', operator, value)

    def _search_amunet_avance(self, operator, value):
        return self._search_amunet_metric('amunet_avance', operator, value)
