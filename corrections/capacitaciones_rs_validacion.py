# Capacitaciones (autorizado Fernando 2026-07-28):
#  1. RS (uid 68 / emp 192): renovar las 25 capacitaciones VENCIDAS -> training_date=hoy,
#     expiry=hoy+12 meses (vuelven a vigente). Se agrega nota de renovacion.
#  2. Validacion (uid 113 / emp 241): cargar SOLO las 4 capacitaciones GENERALES
#     (Induccion, BPM, ISO 13485, Seguridad quimica), vigencia 24 meses.
# El candado de capacitacion esta desactivado; esto es registro/cumplimiento ISO.
from odoo import fields as _f
from dateutil.relativedelta import relativedelta
Reg = env['amunet.registro.capacitacion'].sudo()
today = _f.Date.today()
exp12 = today + relativedelta(months=12)
exp24 = today + relativedelta(months=24)

# 1) RS: renovar vencidas
vencidas = Reg.search([('employee_id', '=', 192), ('state', '=', 'vencida')])
for r in vencidas:
    r.write({'training_date': today, 'expiry_date': exp12,
             'notes': (r.notes or '') + ' | Vigencia renovada 2026-07-28 (autorizado Fernando)'})
print('RS vencidas renovadas:', len(vencidas))

# 2) Validacion: 4 generales
generales = [
    'Induccion a Amunet - Calidad, ISO 13485 y trazabilidad',
    'BPM - Buenas Practicas de Manufactura para dispositivos medicos',
    'ISO 13485:2016 - introduccion para personal operativo',
    'Seguridad quimica y de laboratorio',
]
creadas = 0
for i, cname in enumerate(generales, 1):
    # idempotente: no duplicar si ya existe una nota con ese curso para emp 241
    ya = Reg.search([('employee_id', '=', 241), ('notes', 'ilike', cname[:20])], limit=1)
    if ya:
        continue
    Reg.create({
        'name': 'CAP-VAL-241-%02d' % i,
        'employee_id': 241, 'user_id': 113,
        'training_type': 'presencial',
        'training_date': today, 'expiry_date': exp24,
        'notes': 'Capacitacion general cargada 2026-07-28 (autorizado Fernando): ' + cname,
    })
    creadas += 1
print('Validacion generales creadas:', creadas)

# forzar recompute del estado
Reg.search([('employee_id', 'in', [192, 241])])._compute_state()
env.cr.commit()

# verificacion
for emp, lbl in [(192, 'RS'), (241, 'Validacion')]:
    env.cr.execute("SELECT state, count(*) FROM amunet_registro_capacitacion WHERE employee_id=%s GROUP BY state ORDER BY state", (emp,))
    print(lbl, ':', env.cr.fetchall())
print('LISTO')
