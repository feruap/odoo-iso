# -*- coding: utf-8 -*-
from markupsafe import Markup

WORKCENTERS = [
    ('WC-PESAJE',     'Pesado y preparacion de reactivos',
     ['PRO/BAL/01','PRO/VOR/02','CAL/MIC/02','CAL/MIC/03'], 1),
    ('WC-PRETRAT',    'Pretratamiento y secado de almohadillas',
     ['PRO/HOR/03'], 2),
    ('WC-LAMINADO',   'Laminado de membrana en hoja maestra',
     ['PRO/HOR/03'], 3),
    ('WC-CORTE-HOJA', 'Corte de hoja laminada',
     ['PRO/COH/01','CAL/MIE/01'], 4),
    ('WC-CORTE-TIRA', 'Corte de tiras',
     ['PRO/COT/01','CAL/MIE/01'], 5),
    ('WC-ENSAMBLE',   'Ensamble de cassette',
     ['CAL/LMP/01'], 6),
    ('WC-EMPAQ-PRIM', 'Empaque primario - sellado pouch con desecante',
     ['PRO/SDM/01','PRO/SEL/01','CAL/CNM/01','CAL/CNM/02','CAL/CNM/03','CAL/CNM/04'], 7),
    ('WC-EMPAQ-SEC',  'Empaque secundario - etiquetado y caja',
     ['CAL/LMP/01'], 8),
]

def log(m): print('[WC]', m)

calendar = env.company.resource_calendar_id
log('Calendar default: id=%s name=%s' % (calendar.id, calendar.name))

WC = env['mrp.workcenter']
created = []
for code, name, equip_serials, seq in WORKCENTERS:
    existing = WC.search([('code','=', code)], limit=1)
    if existing:
        wc = existing
        log('WC ya existia: %s id=%s' % (code, wc.id))
    else:
        # Validar equipos
        equips = env['amunet.equipment'].search([('serial_number','in', equip_serials)])
        if len(equips) != len(equip_serials):
            log('ATENCION: equipos faltantes para %s. Pedidos=%s, encontrados=%s' % (
                code, equip_serials, equips.mapped('serial_number')))
        equip_html = '<ul>' + ''.join(
            '<li><b>%s</b> - %s</li>' % (e.serial_number, e.name)
            for e in equips
        ) + '</ul>'
        note_html = (
            '<h4>%s</h4><p>%s</p>'
            '<p><b>Equipos asignados (referencia, sin FK porque mrp.workcenter '
            'no expone integracion con amunet.equipment):</b></p>%s'
        ) % (code, name, equip_html)
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
        log('WC creado: %s id=%s equipos=%s' % (code, wc.id, equips.mapped('serial_number')))
    created.append(wc)

env.cr.commit()
print('TOTAL_WC=%s' % len(created))
for w in created:
    print('WC %s id=%s' % (w.code, w.id))
