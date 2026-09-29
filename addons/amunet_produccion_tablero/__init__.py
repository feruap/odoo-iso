from . import models


def _post_init_plan(env):
    """Las MO ya iniciadas no reciben fecha plan por el compute; se toma su fin programado actual."""
    mos = env['mrp.production'].search([
        ('state', 'in', ('progress', 'to_close')),
        ('amunet_plan_fecha_fin', '=', False),
        ('date_finished', '!=', False),
    ])
    for mo in mos:
        env.cr.execute(
            "UPDATE mrp_production SET amunet_plan_fecha_fin = date_finished WHERE id = %s", (mo.id,))
    env['mrp.production'].invalidate_model(['amunet_plan_fecha_fin'])
