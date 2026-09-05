# -*- coding: utf-8 -*-
"""Tiempos estandar provisionales por estacion y calendario de planta.
Regla (Fernando, 3-sep-2026): la planta hace 3,000 pruebas/dia en ruta corta
y 2,000/dia en ruta larga. Jornada util 480 min -> por estacion en linea:
corta 0.16 min/prueba, larga (laminado) 0.24 min/prueba. Las estaciones con
dos operaciones por lote (AC1, AC2) se reparten el tiempo. Es una muleta:
cuando haya ~10 lotes con "Terminar", pasar la operacion a tiempo automatico.
Uso: odoo shell -d <db> < tiempos_estandar_20260904.py
"""
MIN_POR_UNIDAD = {  # (codigo estacion, prefijo de operacion o None) : minutos por unidad
    ('AMP', None): 0.01,
    ('LSC', 'Laminado'): 0.24,
    ('LSC', None): 0.16,          # corte de hojas maestras
    ('ENC', None): 0.16,
    ('AC1', None): 0.08,          # Acondicionado 1 + Sellado = 0.16
    ('AC2', None): 0.08,          # Acondicionado 2 + Serigrafiado = 0.16
    ('PTT', None): 0.005,
    ('CC', None): 0.02,
    ('SOL', None): 0.05,
    ('PROD', None): 0.16,
}
CAL = env['resource.calendar'].search([('name', 'ilike', 'Jornada Est')], limit=1)
assert CAL, 'falta el calendario Amunet - Jornada Estandar'
Op = env['mrp.routing.workcenter']
tot = 0
for (code, pref), minutos in MIN_POR_UNIDAD.items():
    wc = env['mrp.workcenter'].search([('code', '=', code)], limit=1)
    if not wc:
        print('sin estacion', code); continue
    if wc.resource_calendar_id != CAL:
        wc.resource_calendar_id = CAL
    dom = [('workcenter_id', '=', wc.id)]
    ops = Op.search(dom)
    if pref:
        ops = ops.filtered(lambda o: (o.name or '').startswith(pref))
    else:
        otros = [p for (c, p) in MIN_POR_UNIDAD if c == code and p]
        ops = ops.filtered(lambda o: not any((o.name or '').startswith(p) for p in otros))
    ops.write({'time_mode': 'manual', 'time_cycle_manual': minutos})
    tot += len(ops)
    print('OK', code, pref or '*', len(ops), 'operaciones ->', minutos, 'min/unidad')
# recalcular duracion esperada de las actividades abiertas
wos = env['mrp.workorder'].search([('state', 'not in', ('done', 'cancel')), ('production_id.state', 'not in', ('done', 'cancel'))])
n = 0
for wo in wos:
    try:
        d = wo._get_duration_expected()
        if d and abs((wo.duration_expected or 0) - d) > 0.01:
            wo.with_context(bypass_duration_calculation=True).write({'duration_expected': d}); n += 1
    except Exception as e:
        print('no recalculo', wo.display_name, e)
print('operaciones actualizadas:', tot, '| actividades abiertas recalculadas:', n)
# planear las ordenes confirmadas que no tengan fechas de actividad
mos = env['mrp.production'].search([('state', '=', 'confirmed')])
for mo in mos:
    try:
        mo.button_plan()
        print('planeada', mo.name, [(w.name[:30], str(w.date_start)) for w in mo.workorder_ids[:2]])
    except Exception as e:
        print('no se pudo planear', mo.name, e)
env.cr.commit()
