from . import models


def post_init_hook(env):
    """Asigna calendarios Amunet a empleados activos."""
    cal_estandar = env.ref('amunet_hr_visibility.calendar_amunet_estandar', raise_if_not_found=False)
    cal_medio_dia = env.ref('amunet_hr_visibility.calendar_amunet_medio_dia', raise_if_not_found=False)
    if not cal_estandar:
        return

    kim = env['hr.employee'].search([('name', 'ilike', 'Kimberlin'), ('active', '=', True)], limit=1)

    empleados = env['hr.employee'].search([('active', '=', True)])
    empleados_estandar = empleados - kim
    if empleados_estandar:
        empleados_estandar.write({'resource_calendar_id': cal_estandar.id})
    if kim and cal_medio_dia:
        kim.write({'resource_calendar_id': cal_medio_dia.id})
