from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    exento_retenciones = fields.Boolean(
        string='Exento de retenciones (salario mínimo)',
        default=False,
        # Dato de nomina: solo RRHH. Sin groups, cualquier lectura de la ficha
        # del empleado por un usuario fuera de RRHH cae en la cara publica
        # (hr.employee.public), donde el campo no existe, y Odoo corta con
        # AccessError "no estan disponibles para los perfiles publicos".
        groups='hr.group_hr_user',
        help='Marca esta opción para empleados que perciben salario mínimo. '
             'Se anulan ISR, IMSS cuota obrera y descuentos por faltas.',
    )
