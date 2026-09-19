# -*- coding: utf-8 -*-
"""Alta de los centros de trabajo Lectura y Pretratamiento, e Inyeccion.

Datos confirmados por Jorge (Ensayo) el 18-sep-2026:

  Lectura y Pretratamiento
     Se lee D.O. de conjugado, se pretratan las almohadillas y se secan.
     Tambien se CORTAN las almohadillas: Jorge lo creia y Mery lo confirmo
     el 19-sep-2026. El corte de HOJAS MAESTRAS sigue en Laminado/Secado/Corte;
     lo que se corta aqui son las almohadillas.
     Equipos: Agitador orbital (id 88) y Horno SLW-53 (id 90).
     NO tiene puerta: es el mismo espacio fisico que Soluciones.

  Inyeccion
     Se imprimen conjugados y soluciones de anticuerpo.
     Equipos: manometros 201 y 202.

Van como centros INDEPENDIENTES (lo pidio Jorge explicitamente). El secado
de Laminado/Secado/Corte es de materiales, no de membranas: son operaciones
distintas en areas distintas, por eso no se reutiliza aquel centro.

El corte de almohadillas quedo confirmado por Mery el 19-sep-2026: SI se hace
en Lectura y Pretratamiento. Era el unico punto que Jorge habia dejado abierto.

Idempotente.
"""
WC = env['mrp.workcenter']
CENTROS = [
    ('Lectura y Pretratamiento', 'LYP',
     'Lectura de D.O. de conjugado, pretratado y CORTE de almohadillas, y '
     'secado. El corte de hojas maestras NO es aqui, es en Laminado/Secado/Corte. '
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
