# -*- coding: utf-8 -*-
"""Crea/asegura los 8 work centers HCG con sus equipos vinculados via M2M.

IDEMPOTENTE: si los WC ya existen, los respeta y solo asegura el M2M.
Si los equipos ya estan vinculados, no duplica (Command.set lo maneja).
Si algun equipo no existe en el catalogo, log warning y sigue.
"""
from markupsafe import Markup
from odoo.exceptions import UserError as _DemoGuardError

ALLOWED_DB = "Amunet_testing"
if env.cr.dbname != ALLOWED_DB:
    raise _DemoGuardError(
        "SCRIPT DEMO: solo se ejecuta en BD %r. BD actual: %r. Abortado." % (
            ALLOWED_DB, env.cr.dbname
        )
    )

# code -> (display name, [serial_numbers de equipos], sequence)
WORKCENTERS = {
    'WC-PESAJE':     ('Pesado y preparacion de reactivos',
                      ['PRO/BAL/01','PRO/VOR/02','CAL/MIC/02','CAL/MIC/03'], 1),
    'WC-PRETRAT':    ('Pretratamiento y secado de almohadillas',
                      ['PRO/HOR/03'], 2),
    'WC-LAMINADO':   ('Laminado de membrana en hoja maestra',
                      ['PRO/HOR/03'], 3),
    'WC-CORTE-HOJA': ('Corte de hoja laminada',
                      ['PRO/COH/01','CAL/MIE/01'], 4),
    'WC-CORTE-TIRA': ('Corte de tiras',
                      ['PRO/COT/01','CAL/MIE/01'], 5),
    'WC-ENSAMBLE':   ('Ensamble de cassette',
                      ['CAL/LMP/01'], 6),
    'WC-EMPAQ-PRIM': ('Empaque primario - sellado pouch con desecante',
                      ['PRO/SDM/01','PRO/SEL/01','CAL/CNM/01','CAL/CNM/02','CAL/CNM/03','CAL/CNM/04'], 7),
    'WC-EMPAQ-SEC':  ('Empaque secundario - etiquetado y caja',
                      ['CAL/LMP/01'], 8),
}

def log(m): print('[WC]', m)

calendar = env.company.resource_calendar_id
log('Calendar default: id=%s name=%s' % (calendar.id, calendar.name))

WC = env['mrp.workcenter']
Eq = env['amunet.equipment']

for code, (name, serials, seq) in WORKCENTERS.items():
    # Resolver equipos por serial_number
    eqs = Eq.search([('serial_number', 'in', serials)])
    found_serials = set(eqs.mapped('serial_number'))
    missing = [s for s in serials if s not in found_serials]
    for ms in missing:
        log('  WARN: equipo %s no existe en catalogo (skip)' % ms)

    wc = WC.search([('code', '=', code)], limit=1)
    if wc:
        log('WC ya existia: %s id=%s' % (code, wc.id))
    else:
        # Note legible (no se parsea: solo decorativo/historico)
        eq_html = '<ul>' + ''.join(
            '<li><b>%s</b> - %s</li>' % (e.serial_number, e.name) for e in eqs
        ) + '</ul>'
        note_html = (
            '<h4>%s</h4><p>%s</p>'
            '<p><b>Equipos asignados</b> (relacion formal en M2M '
            'amunet_equipment_ids):</p>%s'
        ) % (code, name, eq_html)
        wc = WC.create({
            'name': name,
            'code': code,
            'sequence': seq,
            'time_efficiency': 100.0,
            'oee_target': 85.0,
            'costs_hour': 50.0,
            'time_start': 0.0,
            'time_stop': 0.0,
            'resource_calendar_id': calendar.id,
            'note': Markup(note_html),
            'company_id': env.company.id,
            'active': True,
        })
        log('WC creado: %s id=%s' % (code, wc.id))

    # Vincular M2M de forma idempotente: 6,0,ids replaza el set completo
    target_ids = sorted(eqs.ids)
    current_ids = sorted(wc.amunet_equipment_ids.ids)
    if target_ids == current_ids:
        log('  M2M %s ya correcto (%s equipos): %s' % (
            code, len(eqs), eqs.mapped('serial_number')))
    else:
        wc.write({'amunet_equipment_ids': [(6, 0, eqs.ids)]})
        log('  M2M %s actualizado (%s equipos): %s' % (
            code, len(eqs), eqs.mapped('serial_number')))

env.cr.commit()
print('=== resumen final ===')
for code in WORKCENTERS:
    wc = env['mrp.workcenter'].search([('code', '=', code)], limit=1)
    if wc:
        print('  %-15s id=%s eqs=%-2s -> %s' % (
            wc.code, wc.id, wc.amunet_equipment_count,
            wc.amunet_equipment_ids.mapped('serial_number')))
