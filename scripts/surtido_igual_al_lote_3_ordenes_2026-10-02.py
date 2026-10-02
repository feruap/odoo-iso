# -*- coding: utf-8 -*-
"""Tres ordenes abiertas: la cantidad surtida se iguala a la de los lotes.

Mismo criterio que en 0826/01/ECO: manda lo que salio fisicamente del almacen.

PERO CON UNA PRECISION QUE IMPORTA: "lo que dice el lote" es lo que tiene LOTE
ASIGNADO. En 0926/01/ICN hay tres lineas de 11 unidades SIN lote, creadas por Produccion
el 30-sep a las 19:06 -- las tres en el mismo segundo-, en estado partially_available.
Eso es reserva pendiente de asignarle lote, no material que haya salido del almacen.
Contarlas como surtidas diria que salieron 359 cuando solo 348 estan identificadas.

Asi que la suma IGNORA las lineas sin lote. En MPBOL01, MPCAR59 y STGOT04 de esa orden
la cantidad surtida ya coincide con lo que tiene lote (348) y no se tocan: el descuadre
era de la medicion, no del dato.

QUE SI SE CORRIGE:

  0826/01/DCZ   MICAJ01   210 -> 375    se le anadio un segundo lote y el campo no siguio
                STDSC01  3720 -> 3750   igual
  0926/01/CCF   MICAJ01   375 -> 210    aqui al reves: el campo quedo por ENCIMA
                STDSC01  3750 -> 3709   igual
  0926/01/ICN   STDSC01   348 -> 359    un solo lote, con 359
                SPHMC59 147.4 -> 143.6  la hoja: el campo decia mas de lo que salio

El lote CAJ01092601 aparece en OCHO ordenes distintas: es un lote de cajas que se reparte
entre varias. No es que las ordenes se cruzaran; es consumo normal de un lote grande, y
por eso el campo de cada orden se desfasa cuando se reparte.

Idempotente. Escribe con amunet_supply_internal, la puerta que el modulo deja para el
flujo interno (ese campo esta reservado a Almacen).
"""

ORDENES = ['0826/01/DCZ', '0926/01/CCF', '0926/01/ICN']

total, saltadas = [], []
for nombre in ORDENES:
    mo = env['mrp.production'].search([('name', '=', nombre)], limit=1)
    if not mo:
        print('[!] no existe %s' % nombre); continue
    print('\n%s   %s   state=%s   %s pz' % (nombre, mo.product_id.default_code, mo.state, mo.product_qty))
    cambios = []
    for m in mo.move_raw_ids.sorted(lambda x: x.product_id.default_code or ''):
        con_lote = m.move_line_ids.filtered(lambda ml: ml.lot_id)
        sin_lote = m.move_line_ids.filtered(lambda ml: not ml.lot_id and ml.quantity)
        en_lotes = sum(con_lote.mapped('quantity'))
        surtida = m.amunet_qty_supplied or 0.0
        nota_sin = ('   (+%s sin lote, NO se cuentan)' % sum(sin_lote.mapped('quantity'))) if sin_lote else ''
        if abs(en_lotes - surtida) < 0.001:
            print('  [=] %-9s %s%s' % (m.product_id.default_code, surtida, nota_sin))
            if sin_lote:
                saltadas.append((nombre, m.product_id.default_code, sum(sin_lote.mapped('quantity'))))
            continue
        lotes = ', '.join('%s: %s' % (ml.lot_id.name, ml.quantity) for ml in con_lote)
        m.with_context(amunet_supply_internal=True).amunet_qty_supplied = en_lotes
        cambios.append((m.product_id.default_code, surtida, en_lotes, lotes))
        print('  [+] %-9s %s -> %s%s   (%s)' % (
            m.product_id.default_code, surtida, en_lotes, nota_sin, lotes))
    if cambios:
        filas = ''.join('<tr><td>%s</td><td style="text-align:right">%s</td>'
                        '<td style="text-align:right"><b>%s</b></td><td>%s</td></tr>' % c for c in cambios)
        mo.message_post(body=(
            '<p><b>Cantidad surtida igualada a la de los lotes</b> en %s componente(s).</p>'
            '<table border="1" cellpadding="4" style="border-collapse:collapse">'
            '<tr><th>Componente</th><th>Decia</th><th>Ahora</th><th>Lotes</th></tr>%s</table>'
            '<p>Manda lo que salio fisicamente del almacen, que es lo que registran los '
            'lotes. Las lineas SIN lote no se cuentan: son reserva pendiente de asignar, '
            'no material surtido. Indicacion de Mery, 02-oct-2026.</p>') % (len(cambios), filas))
        total += cambios

env.cr.commit()

print('\n=== COMPROBACION ===')
for nombre in ORDENES:
    mo = env['mrp.production'].search([('name', '=', nombre)], limit=1)
    mo.invalidate_recordset()
    malos = []
    for m in mo.move_raw_ids:
        en_lotes = sum(m.move_line_ids.filtered(lambda ml: ml.lot_id).mapped('quantity'))
        if abs(en_lotes - (m.amunet_qty_supplied or 0.0)) > 0.001:
            malos.append('%s (%s vs %s)' % (m.product_id.default_code, m.amunet_qty_supplied, en_lotes))
    print('  %-14s %s' % (nombre, 'cuadrada' if not malos else 'SIGUE: ' + ', '.join(malos)))

print('\ncomponentes corregidos: %s' % len(total))
if saltadas:
    print('\nlineas SIN LOTE que quedan pendientes de asignar (no se contaron):')
    for o, c, q in saltadas:
        print('   %-14s %-9s %s unidades' % (o, c, q))
