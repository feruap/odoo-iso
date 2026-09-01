# -*- coding: utf-8 -*-
from odoo import models, fields


class AmunetCumplimiento(models.Model):
    """
    Vista SQL de cumplimiento de capacitación.
    Cruza empleado × cursos requeridos por su plan y muestra el estado real.
    ISO 13485:2016 - Clausula 6.2 (Competencia del personal).
    """
    _name = 'amunet.cumplimiento'
    _description = 'Cumplimiento de Capacitación por Empleado (ISO 13485 6.2)'
    _auto = False
    _order = 'employee_id, plan_id, curso_id'

    employee_id = fields.Many2one('hr.employee', string='Empleado', readonly=True)
    department_id = fields.Many2one('hr.department', string='Departamento', readonly=True)
    job_id = fields.Many2one('hr.job', string='Puesto', readonly=True)
    plan_id = fields.Many2one('amunet.plan.estudios', string='Plan', readonly=True)
    curso_id = fields.Many2one('amunet.curso', string='Curso', readonly=True)
    obligatorio = fields.Boolean(string='Obligatorio', readonly=True)
    estado = fields.Selection([
        ('vigente', 'Vigente'),
        ('por_vencer', 'Por vencer'),
        ('vencida', 'Vencida'),
        ('sin_iniciar', 'Pendiente'),
    ], string='Estado', readonly=True)
    expiry_date = fields.Date(string='Vence', readonly=True)

    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW amunet_cumplimiento AS
            WITH mejor AS (
                SELECT
                    employee_id,
                    hr_course_id,
                    CASE
                        WHEN bool_or(state = 'vigente') THEN 'vigente'
                        WHEN bool_or(state = 'proxima') THEN 'por_vencer'
                        ELSE 'vencida'
                    END AS estado,
                    MAX(expiry_date) AS expiry_date
                FROM amunet_registro_capacitacion
                WHERE state != 'cancelada'
                  AND hr_course_id IS NOT NULL
                GROUP BY employee_id, hr_course_id
            )
            SELECT
                ROW_NUMBER() OVER (ORDER BY e.id, p.id, l.curso_id) AS id,
                e.id AS employee_id,
                v.department_id,
                v.job_id,
                p.id AS plan_id,
                l.curso_id,
                l.obligatorio,
                COALESCE(m.estado, 'sin_iniciar') AS estado,
                m.expiry_date
            FROM hr_employee e
            JOIN hr_version v ON v.employee_id = e.id
                AND v.active = true
                AND v.departure_date IS NULL
            JOIN amunet_plan_job_rel pj ON pj.job_id = v.job_id
            JOIN amunet_plan_estudios p ON p.id = pj.plan_id AND p.active = true
            JOIN amunet_plan_estudios_linea l ON l.plan_id = p.id
            LEFT JOIN mejor m ON m.employee_id = e.id AND m.hr_course_id = l.curso_id
            WHERE e.active = true
              AND (
                NOT EXISTS (
                    SELECT 1 FROM amunet_plan_department_rel pd
                    WHERE pd.plan_id = p.id
                )
                OR v.department_id IN (
                    SELECT pd.department_id FROM amunet_plan_department_rel pd
                    WHERE pd.plan_id = p.id
                )
              )
        """)
