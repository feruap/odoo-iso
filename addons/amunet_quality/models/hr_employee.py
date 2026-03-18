# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_code = fields.Char(
        string="Código de Empleado (Firma QC)",
        help="Código único para firmas en reportes de calidad (exactamente 2 dígitos numéricos)."
    )

    @api.constrains('employee_code')
    def _check_employee_code(self):
        for record in self:
            if record.employee_code:
                if len(record.employee_code) != 2 or not record.employee_code.isdigit():
                    raise ValidationError("El Código de Empleado debe ser exactamente de 2 dígitos numéricos (ej. '01', '15').")

    @api.model_create_multi
    def create(self, vals_list):
        employees = super(HrEmployee, self).create(vals_list)
        # Sincronizar el código al usuario si se crea el empleado junto con el usuario
        for employee in employees:
            if employee.user_id and employee.employee_code:
                employee.user_id.sudo().write({'employee_code': employee.employee_code})
        return employees

    def write(self, vals):
        res = super(HrEmployee, self).write(vals)
        # Sincronizar cuando se modifica el código o se vincula un usuario
        if 'employee_code' in vals or 'user_id' in vals:
            for employee in self:
                if employee.user_id:
                    # Si se borró el código en el empleado, también se borra en el usuario?
                    # Por seguridad, si el empleado tiene código, se prioriza el código del empleado.
                    if employee.employee_code:
                        employee.user_id.sudo().write({'employee_code': employee.employee_code})
        return res
