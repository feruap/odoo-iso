"""El jefe de Practicantes Soluciones pasa de Alondra a Julissa.

Autorizado por Mery el 28-sep-2026. Acompana al cambio de codigo que permite
firmar la supervision al jefe directo Y al jefe de ese jefe (dos niveles).

Con los dos juntos, las soluciones que elabora el practicante las firma
**Julissa** normalmente, y **Alondra la cubre** si no esta.

Es un cambio de ORGANIGRAMA, no solo de permisos: afecta los reportes de
capacitacion por area. RRHH avisado el mismo dia.

Idempotente: si ya esta puesto, no hace nada.
"""

"""El jefe de Practicantes Soluciones pasa a ser Julissa. STAGING."""
E = env['hr.employee'].sudo()
prac = E.search([('user_id.login','=','practicante.sol@amunet.com.mx')], limit=1)
jul  = E.search([('user_id.login','=','soluciones@amunet.com.mx')], limit=1)
assert prac and jul, 'falta el practicante o Julissa'
print('ANTES : %s -> jefe %s' % (prac.name, prac.parent_id.name or '(sin jefe)'))
prac.write({'parent_id': jul.id})
print('DESPUES: %s -> jefe %s (y su jefa: %s)' % (
    prac.name, prac.parent_id.name, prac.parent_id.parent_id.name or '(ninguna)'))
env.cr.commit()
