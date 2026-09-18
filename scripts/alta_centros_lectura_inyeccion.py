# -*- coding: utf-8 -*-
"""Alta de los centros de trabajo Lectura y Pretratamiento, e Inyeccion.

Datos confirmados por Jorge (Ensayo) el 18-sep-2026:

  Lectura y Pretratamiento
     Se lee D.O. de conjugado, se pretratan las almohadillas y se secan.
     Equipos: Agitador orbital (id 88) y Horno SLW-53 (id 90).
     NO tiene puerta: es el mismo espacio fisico que Soluciones.

  Inyeccion
     Se imprimen conjugados y soluciones de anticuerpo.
     Equipos: manometros 201 y 202.

Van como centros INDEPENDIENTES (lo pidio Jorge explicitamente). El secado
de Laminado/Secado/Corte es de materiales, no de membranas: son operaciones
distintas en areas distintas, por eso no se reutiliza aquel centro.

PENDIENTE (no bloquea): el corte de almohadillas. Jorge cree que se hace en
Lectura y Pretratamiento, pero pidio confirmarlo con Alondra antes de
registrarlo. Mientras no se confirme, no se le asigna esa operacion.

Idempotente.
"""
WC = env['mrp.workcenter']
CENTROS = [
    ('Lectura y Pretratamiento', 'LYP',
     'Lectura de D.O. de conjugado, pretratado de almohadillas y secado. '
     'Mismo espacio fisico que Soluciones, sin separacion (no tiene puerta). '
     'Equipos: Agitador orbital (88) y Horno SLW-53 (90).'),
    ('Inyección', 'INY',
     'Impresion de conjugados y soluciones de anticuerpo. '
     'Equipos: manometros 201 y 202.'),
]
for nombre, code, nota in CENTROS:
    wc = WC.search(['|', ('name', '=', nombre), ('code', '=', code)], limit=1)
    vals = {'name': nombre, 'code': code, 'active': True,
            'time_efficiency': 100.0, 'costs_hour': 0.0, 'note': nota}
    if wc:
        wc.sudo().write(vals)
        print('ACTUALIZADO  id=%-4s %-28s %s' % (wc.id, nombre, code))
    else:
        wc = WC.sudo().create(vals)
        print('CREADO       id=%-4s %-28s %s' % (wc.id, nombre, code))

# Equipos que Ensayo asocia a cada area (por departamento, que es como se
# relacionan hoy: amunet.equipment no tiene campo de centro de trabajo).
Eq = env['amunet.equipment'].sudo()
for depto in ('LECTURA Y PRETRATAMIENTO', 'INYECCIÓN'):
    eqs = Eq.search([('department', '=', depto)])
    print('EQUIPOS en %-26s %s' % (
        depto, ', '.join('%s (%s)' % (e.name, e.id) for e in eqs) or '(ninguno)'))

env.cr.commit()
print('COMMIT OK')
