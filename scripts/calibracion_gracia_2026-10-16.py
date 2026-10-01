# -*- coding: utf-8 -*-
"""Gracia de calibracion: 2026-09-30 -> 2026-10-16. QUINTA prorroga.

POR QUE SE EXTIENDE HOY. La gracia vencio AYER (30-sep) y el candado se encendio. Hoy
quedo bloqueado el preflight PREF/2026/00042 de la orden 1026/01/VID (DMVID01 VITAMINET
D, 940 piezas): producto, cantidad, ruta, BOM, componentes y las 8 operaciones pasan;
lo unico que lo detiene son 8 pasos de "Equipo/metrologia", todos con el mismo motivo:
sin calibracion registrada. Equipos que aparecen: ALM/REF/01, ALM/TER/01, PRO/IMP/01,
PRO/HOR/03, PRO/COT/01, PRO/TER/04, PRO/SEC/01, PRO/SEL/01.

Mery autorizo 15 dias de colchon el 01-oct-2026. 15 dias contados desde hoy = 16-oct.

EL DATO QUE HAY QUE TENER A LA VISTA: siguen siendo 71 equipos que requieren
calibracion y CERO certificados cargados -- la tabla amunet_equipment_calibration esta
literalmente vacia-. Secuencia de prorrogas:

    31-jul -> 07-ago -> 31-ago -> 30-sep -> 16-oct

Tres meses desde el primer aviso sin un solo archivo subido. La gracia dejo de ser un
puente y es el estado normal: el candado que garantiza fabricar con equipo calibrado
lleva tres meses apagado, y es un control de Cofepris/ISO 13485.

El area responsable es ENSAYO, no Calidad ni Metrologia. Los avisos de julio fueron al
buzon equivocado y eso explica parte del silencio.

Se aplica en produccion Y en staging para que no divergan.
"""
from datetime import date

NUEVA = '2026-10-16'
CLAVE = 'amunet.calibration.grace.deadline'

ICP = env['ir.config_parameter'].sudo()
previa = ICP.get_param(CLAVE, default='(sin valor)')
print('gracia antes:  %s' % previa)
print('hoy:           %s' % date.today().isoformat())
if previa == NUEVA:
    print('ya estaba en %s' % NUEVA)
else:
    ICP.set_param(CLAVE, NUEVA)
    print('gracia ahora:  %s' % ICP.get_param(CLAVE))
env.cr.commit()

# --- el panorama, para que quede en el log ---
eqs = env['amunet.equipment'].search([('calibration_required', '=', True)])
cals = env['amunet.equipment.calibration'].search([])
vig = cals.filtered(lambda c: c.state == 'done' and c.expiration_date
                    and c.expiration_date >= date.today())
print('\nequipos que requieren calibracion: %s' % len(eqs))
print('certificados cargados (cualquier estado): %s' % len(cals))
print('certificados VIGENTES: %s' % len(vig))

# --- re-correr los chequeos de los preflights bloqueados ---
pres = env['amunet.pilot.preflight'].search([('state', '=', 'blocked')])
print('\npreflights bloqueados: %s' % len(pres))
for p in pres.sorted('id'):
    antes = p.state
    bloqueos_antes = len(p.line_ids.filtered(lambda l: l.status == 'block'))
    try:
        p.action_run_checks()
        env.cr.commit()
    except Exception as e:
        print('  %-16s [!] no se pudo recorrer: %s' % (p.name, str(e)[:60]))
        continue
    p.invalidate_recordset()
    bloqueos = p.line_ids.filtered(lambda l: l.status == 'block')
    print('  %-16s %s -> %s   bloqueos: %s -> %s' % (
        p.name, antes, p.state, bloqueos_antes, len(bloqueos)))
    for l in bloqueos:
        print('        sigue bloqueado: %s' % (l.name or '')[:72])
        primera = (l.detail or '').strip().split('\n')
        for d in primera[:3]:
            if d.strip():
                print('            %s' % d.strip()[:80])

print('\n=== RESULTADO ===')
for p in env['amunet.pilot.preflight'].search([('id', 'in', pres.ids)]).sorted('id'):
    print('  %-16s %s' % (p.name, p.state))
