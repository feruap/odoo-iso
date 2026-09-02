from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    exento_retenciones = fields.Boolean(
        string='Exento de retenciones (salario mínimo)',
        default=False,
        help='Marca esta opción para empleados que perciben salario mínimo. '
             'Se anulan ISR, IMSS cuota obrera y descuentos por faltas.',
    )
