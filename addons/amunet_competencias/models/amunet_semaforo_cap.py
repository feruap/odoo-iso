# -*- coding: utf-8 -*-
from odoo import models, fields


class AmunetSemaforoCap(models.Model):
    _name = 'amunet.semaforo.cap'
    _description = 'Semáforo de capacitación por empleado y curso requerido'
    _auto = False
    _order = 'employee_name, course_name'

    employee_id = fields.Many2one('hr.employee', string='Empleado', readonly=True)
    employee_name = fields.Char(string='Nombre empleado', readonly=True)
    department_id = fields.Many2one('hr.department', string='Área', readonly=True)
    course_id = fields.Many2one('hr.training.course', string='Curso', readonly=True)
    course_name = fields.Char(string='Nombre curso', readonly=True)
    registro_id = fields.Many2one('amunet.registro.capacitacion', string='Registro', readonly=True)
    expiry_date = fields.Date(string='Vence', readonly=True)
    days_to_expiry = fields.Integer(string='Días restantes', readonly=True)
    estado = fields.Selection([
        ('vigente', 'Vigente'),
        ('proxima', 'Por vencer'),
        ('vencida', 'Vencida'),
        ('faltante', 'Sin registro'),
    ], string='Estado', readonly=True)

    def init(self):
        self.env.cr.execute("DROP VIEW IF EXISTS amunet_semaforo_cap")
        self.env.cr.execute("""
CREATE VIEW amunet_semaforo_cap AS
WITH emp_dept AS (
    -- Departamento más reciente de cada empleado en sus registros de cap
    SELECT DISTINCT ON (r.employee_id)
        r.employee_id,
        r.department_id
    FROM amunet_registro_capacitacion r
    WHERE r.department_id IS NOT NULL AND r.employee_id IS NOT NULL
    ORDER BY r.employee_id, r.create_date DESC
),
mejor_registro AS (
    -- Último registro vigente por empleado x curso (el de mayor expiry_date)
    SELECT DISTINCT ON (rc.employee_id, rc.hr_course_id)
        rc.id,
        rc.employee_id,
        rc.hr_course_id,
        rc.expiry_date
    FROM amunet_registro_capacitacion rc
    WHERE rc.hr_course_id IS NOT NULL AND rc.employee_id IS NOT NULL
    ORDER BY rc.employee_id, rc.hr_course_id, rc.expiry_date DESC
),
req_por_empleado AS (
    -- Expandir requisitos a empleados activos
    SELECT req.id AS requisito_id, req.course_id, e.id AS employee_id
    FROM amunet_curso_requisito req
    JOIN hr_employee e ON e.active = true AND e.name NOT ILIKE '%practicante%'
    LEFT JOIN emp_dept ed ON ed.employee_id = e.id
    WHERE (
        -- Para todos: aplica_todos y el dept del empleado NO está excluido
        (req.aplica_todos = true
         AND NOT EXISTS (
             SELECT 1 FROM amunet_req_excl_dept_rel ex
             WHERE ex.requisito_id = req.id AND ex.department_id = ed.department_id
         )
        )
        OR
        -- Por departamento específico
        EXISTS (
            SELECT 1 FROM amunet_req_dept_rel rd
            WHERE rd.requisito_id = req.id AND rd.department_id = ed.department_id
        )
        OR
        -- Por empleado específico
        EXISTS (
            SELECT 1 FROM amunet_req_emp_rel re
            WHERE re.requisito_id = req.id AND re.employee_id = e.id
        )
    )
)
SELECT
    ROW_NUMBER() OVER (ORDER BY e.name, c.name) AS id,
    e.id AS employee_id,
    e.name AS employee_name,
    ed.department_id,
    req.course_id,
    c.name AS course_name,
    mr.id AS registro_id,
    mr.expiry_date,
    (mr.expiry_date - CURRENT_DATE)::integer AS days_to_expiry,
    CASE
        WHEN mr.id IS NULL THEN 'faltante'
        WHEN mr.expiry_date IS NULL THEN 'faltante'
        WHEN mr.expiry_date < CURRENT_DATE THEN 'vencida'
        WHEN mr.expiry_date <= CURRENT_DATE + INTERVAL '90 days' THEN 'proxima'
        ELSE 'vigente'
    END AS estado
FROM req_por_empleado req
JOIN hr_employee e ON e.id = req.employee_id
JOIN hr_training_course c ON c.id = req.course_id
LEFT JOIN emp_dept ed ON ed.employee_id = e.id
LEFT JOIN mejor_registro mr ON mr.employee_id = e.id AND mr.hr_course_id = req.course_id
""")
