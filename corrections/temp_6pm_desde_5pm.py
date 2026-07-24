# -*- coding: utf-8 -*-
# Habilita la captura del turno de las 6pm (18.0) desde las 5pm (60 min antes)
# en todas las areas del Monitor de Temperatura. Ajusta tambien las tomas de HOY
# ya generadas para que abran a las 5pm. Pedido de Fernando 2026-07-13.
# Idempotente. El campo early_minutes/early_open_minutes lo agrego el modulo
# amunet_monitor_temperatura v19.0.1.19.0.
from odoo import fields
Slot = env['amunet.temp.slot']
Read = env['amunet.temp.reading']

slots = Slot.search([('time_hour', '=', 18.0)])
slots.write({'early_minutes': 60})
print("turnos 6pm puestos a 60 min:", len(slots))

today = fields.Date.context_today(Read)
reads = Read.search([('date', '=', today), ('scheduled_time', '=', 18.0)])
reads.with_context(amunet_temp_internal=True).write({'early_open_minutes': 60})
print("tomas de hoy (6pm) ajustadas:", len(reads))

env.cr.commit()

# Verificacion
m = Slot.search([('time_hour', '=', 18.0), ('early_minutes', '=', 60)])
print("VERIF: turnos 6pm con early=60 ->", len(m), "de", len(slots))
r = Read.search([('date', '=', today), ('scheduled_time', '=', 18.0)], limit=1)
if r:
    r._compute_capture_available()
    print("Ejemplo:", r.area_id.code, "6pm se habilita:", r.window_open_label)
print("LISTO")
