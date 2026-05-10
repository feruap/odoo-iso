# -*- coding: utf-8 -*-
"""Espacia los timestamps reales de las 8 WO de MO 7 segun los tiempos
planificados, para que coincidan con un dia de produccion realista."""
from datetime import datetime
from odoo.exceptions import UserError as _DemoGuardError

ALLOWED_DB = "Amunet_testing"
if env.cr.dbname != ALLOWED_DB:
    raise _DemoGuardError(
        "SCRIPT DEMO: solo se ejecuta en BD %r. BD actual: %r." % (
            ALLOWED_DB, env.cr.dbname
        )
    )

# (wc_code, start_iso, end_iso) para MO 7. Hora local Mexico (CDT/UTC-5).
# Guardado como UTC-5 -> UTC: agregar 5 horas a las horas locales.
PLAN = [
    ('WC-PESAJE',     '2026-05-10 13:00:00', '2026-05-10 14:00:00'),  # 08:00-09:00 MX
    ('WC-PRETRAT',    '2026-05-10 14:00:00', '2026-05-10 16:00:00'),  # 09:00-11:00
    ('WC-LAMINADO',   '2026-05-10 16:00:00', '2026-05-10 17:30:00'),  # 11:00-12:30
    ('WC-CORTE-HOJA', '2026-05-10 18:30:00', '2026-05-10 19:30:00'),  # 13:30-14:30 (despues de comida)
    ('WC-CORTE-TIRA', '2026-05-10 19:30:00', '2026-05-10 21:00:00'),  # 14:30-16:00
    ('WC-ENSAMBLE',   '2026-05-11 13:00:00', '2026-05-11 17:00:00'),  # dia 2: 08:00-12:00
    ('WC-EMPAQ-PRIM', '2026-05-11 18:00:00', '2026-05-11 21:00:00'),  # 13:00-16:00
    ('WC-EMPAQ-SEC',  '2026-05-11 21:00:00', '2026-05-11 22:30:00'),  # 16:00-17:30
]

def log(m): print('[WO-TIMES]', m)

mo = env['mrp.production'].browse(7)
log('MO: %s id=%s state=%s wo=%s' % (mo.name, mo.id, mo.state, len(mo.workorder_ids)))

# Mapear WC code -> WO
wos_by_code = {}
for wo in mo.workorder_ids:
    code = wo.workcenter_id.code
    if code in wos_by_code:
        log('  WARN: 2 WOs en mismo WC %s, tomando la 1ra' % code)
    else:
        wos_by_code[code] = wo

for wc_code, start_iso, end_iso in PLAN:
    wo = wos_by_code.get(wc_code)
    if not wo:
        log('  WO para %s no encontrada' % wc_code)
        continue
    start_dt = datetime.fromisoformat(start_iso)
    end_dt = datetime.fromisoformat(end_iso)
    duration_min = (end_dt - start_dt).total_seconds() / 60.0
    wo.write({
        'date_start': start_dt,
        'date_finished': end_dt,
        'duration': duration_min,
    })
    log('  %s WO id=%s: %s -> %s (%s min)' % (wc_code, wo.id, start_iso, end_iso, duration_min))

env.cr.commit()
log('--- timestamps post-update ---')
for wo in mo.workorder_ids.sorted(lambda w: w.date_start or False):
    log('  WO id=%s %s | start=%s end=%s dur=%s' % (
        wo.id, wo.workcenter_id.code, wo.date_start, wo.date_finished, wo.duration))
print('TIMES_DONE')
