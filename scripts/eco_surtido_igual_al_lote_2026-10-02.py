# -*- coding: utf-8 -*-
"""0826/01/ECO: la cantidad surtida se iguala a la que de verdad salio del almacen.

EL DESCUADRE. En la orden de E. coli (DLECO01 ECOHEM-ADN, 84 piezas) siete componentes
tenian la "cantidad surtida" por debajo de lo que dicen sus lotes:

    MICAJ07, STACM01, STCNL01, STCPL15, STRDI01     4  ->  7
    MPBOL05                                        48  -> 84
    STDSC01                                        96  -> 168

QUE PASO, y lo dice la proporcion: 4/7, 48/84 y 96/168 son el MISMO numero (0.571). El
surtido se capturo cuando la orden era de 48 piezas y despues subio a 84. Los lotes se
movieron por la cantidad nueva; el campo de cantidad surtida se quedo con la vieja.

MANDA EL LOTE (indicacion de Mery): lo que salio fisicamente del almacen es lo que
registran las lineas de movimiento, con su lote y su cantidad. La "cantidad surtida" es
un campo de captura, y cuando los dos no coinciden, el que describe la realidad es el
movimiento.

Dos componentes ya cuadraban y NO se tocan: MIFUN03 (7=7) y STBBM01 (84=84).

Se escribe con el contexto amunet_supply_internal, que es la puerta que el propio modulo
deja para el flujo interno: ese campo esta reservado a Almacen y Produccion no lo captura.

Idempotente: solo escribe lo que no coincide, y comprueba al final.
"""

ORDEN = '0826/01/ECO'

mo = env['mrp.production'].search([('name', '=', ORDEN)], limit=1)
assert mo, 'no existe la orden %s' % ORDEN
print('%s   producto=%s   state=%s   %s pz' % (
    mo.name, mo.product_id.default_code, mo.state, mo.product_qty))

cambios = []
for m in mo.move_raw_ids.sorted(lambda x: x.product_id.default_code or ''):
    en_lotes = sum(m.move_line_ids.mapped('quantity'))
    surtida = m.amunet_qty_supplied or 0.0
    if abs(en_lotes - surtida) < 0.001:
        print('  [=] %-9s %s = %s' % (m.product_id.default_code, surtida, en_lotes))
        continue
    lotes = ', '.join('%s: %s' % (ml.lot_id.name or '(sin lote)', ml.quantity)
                      for ml in m.move_line_ids)
    m.with_context(amunet_supply_internal=True).amunet_qty_supplied = en_lotes
    cambios.append((m.product_id.default_code, surtida, en_lotes, lotes))
    print('  [+] %-9s %s -> %s   (%s)' % (m.product_id.default_code, surtida, en_lotes, lotes))

if cambios:
    filas = ''.join(
        '<tr><td>%s</td><td style="text-align:right">%s</td>'
        '<td style="text-align:right"><b>%s</b></td><td>%s</td></tr>' % c for c in cambios)
    mo.message_post(body=(
        '<p><b>Cantidad surtida igualada a la de los lotes</b> en %s componente(s).</p>'
        '<table border="1" cellpadding="4" style="border-collapse:collapse">'
        '<tr><th>Componente</th><th>Decia</th><th>Ahora</th><th>Lotes que se movieron</th></tr>'
        '%s</table>'
        '<p>La cantidad surtida venia de cuando la orden era de 48 piezas; despues subio '
        'a 84 y los lotes se movieron por la cantidad nueva. Manda lo que salio '
        'fisicamente del almacen, que es lo que registran los lotes. Indicacion de Mery, '
        '02-oct-2026.</p>') % (len(cambios), filas))

env.cr.commit()

print('\n=== COMO QUEDO ===')
mo.invalidate_recordset()
pendientes = 0
for m in mo.move_raw_ids.sorted(lambda x: x.product_id.default_code or ''):
    en_lotes = sum(m.move_line_ids.mapped('quantity'))
    ok = abs(en_lotes - (m.amunet_qty_supplied or 0.0)) < 0.001
    pendientes += 0 if ok else 1
    print('  %-9s surtida=%-8s en lotes=%-8s %s' % (
        m.product_id.default_code, m.amunet_qty_supplied, en_lotes, 'OK' if ok else '<-- SIGUE DESCUADRADO'))
print('\ncomponentes corregidos: %s   descuadrados que quedan: %s' % (len(cambios), pendientes))
