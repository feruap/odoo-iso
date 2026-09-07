from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    exento_retenciones = fields.Boolean(
        string='Exento de retenciones (salario mínimo)',
        default=False,
        # Dato de nomina: solo RRHH. Sin groups, cualquier lectura de la ficha
        # del empleado por un usuario fuera de RRHH cae en la cara publica
        # (hr.employee.public), donde el campo no existia, y Odoo corta con
        # AccessError "no estan disponibles para los perfiles publicos".
        groups='hr.group_hr_user',
        help='Marca esta opción para empleados que perciben salario mínimo. '
             'Se anulan ISR, IMSS cuota obrera y descuentos por faltas.',
    )


class HrEmployeePublic(models.Model):
    """Espejo del campo en el perfil PUBLICO del empleado.

    Odoo 17+ deriva la vista de `hr.employee.public` del formulario de
    `hr.employee`. Un campo agregado a ese formulario que no exista en el
    modelo publico rompe la ficha de TODOS los empleados para usuarios sin
    RRHH ("Los campos ... no estan disponibles para los perfiles publicos").

    El `groups` del campo en hr.employee ya evita que el formulario lo pida;
    declararlo TAMBIEN aqui es la red de seguridad: cualquier otra lectura
    del modelo publico (lista, kanban, busqueda, RPC) que lo incluya deja de
    tronar. `hr.employee.public` es una vista SQL y Odoo lo mapea solo a la
    columna e.exento_retenciones de hr_employee.
    """
    _inherit = 'hr.employee.public'

    exento_retenciones = fields.Boolean(
        string='Exento de retenciones (salario mínimo)',
        readonly=True,
        groups='hr.group_hr_user',
    )
