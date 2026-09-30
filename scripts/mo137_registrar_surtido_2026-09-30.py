"""0926/01/CCF: registra el surtido de las 150 piezas extra que Almacen ya entrego.

Autorizado por Mery el 30-sep-2026, despues de subir la orden de 3,600 a 3,750 piezas.
Confirmo que el material YA SALIO FISICAMENTE del almacen y lo que falta es registrarlo.

EL CAMPO ES DE ALMACEN, Y ESO IMPORTA. stock_move.write() tiene un candado: solo el
personal de Almacen puede capturar 'Cantidad surtida' y 'Lote', porque esa cifra es el
ACTA de que el material salio del anaquel. Quien la captura declara que lo entrego.

Se escribe con el contexto amunet_supply_internal, que es la puerta prevista para las
escrituras del propio flujo. No se relaja ningun grupo ni se le da el permiso a nadie: es
una captura puntual, autorizada por Mery, y queda anotada en el historial de la orden con
quien la autorizo y por que.

POR QUE SE ANOTA EN EL CHATTER. Un numero de surtido sin movimiento de inventario es el
defecto que llevamos toda la semana corrigiendo: en 0926/01/VPL el sistema decia 216
surtidas y fisicamente habia 172, y en QC/2026/00514 un cero mando 60 pruebas a Desechos.
Si mas adelante alguien encuentra una diferencia en estos seis componentes, el historial
dice de donde salio la cifra.

QUE SE REGISTRA, la diferencia entre lo que la orden pide ahora y lo que ya estaba surtido:

    MPCAC07   3600 -> 3750    +150
    STBTR02   3535 -> 3750    +215   <- 215 y no 150: ya venia con 65 pendientes
    STHIS01   3600 -> 3750    +150
    STDSC01   3600 -> 3750    +150
    MPBOL01   3600 -> 3750    +150
    MICAJ01    360 ->  375     +15

Idempotente: si el surtido ya coincide con lo que pide la orden, no hace nada.
"""
from markupsafe import Markup

MO = env['mrp.production'].sudo()
mo = MO.browse(137)
assert mo.exists() and mo.name == '0926/01/CCF', 'el id 137 no es 0926/01/CCF'
assert abs(mo.product_qty - 3750.0) < 0.001, 'la orden no pide 3750, pide %s' % mo.product_qty

print('=== %s: registrando el surtido ===' % mo.name)
cambios = []
for m in mo.move_raw_ids:
    if m.state == 'cancel':
        continue
    antes = m.amunet_qty_supplied or 0.0
    debe = m.product_uom_qty
    if abs(antes - debe) < 0.001:
        print('   [ya] %-12s surtido %8.1f = lo que pide' % (m.product_id.default_code or '?', antes))
        continue
    if antes > debe:
        print('   [ojo] %-12s surtido %8.1f es MAYOR que lo que pide %8.1f: no se toca' % (
            m.product_id.default_code or '?', antes, debe))
        continue
    m.with_context(amunet_supply_internal=True).write({'amunet_qty_supplied': debe})
    cambios.append((m.product_id.default_code or '?', antes, debe, debe - antes))
    print('   [ok] %-12s %8.1f -> %8.1f   (+%.1f)' % (m.product_id.default_code or '?', antes, debe, debe - antes))

if cambios:
    filas = ''.join(
        '<tr><td>%s</td><td class="text-end">%g</td><td class="text-end">%g</td>'
        '<td class="text-end"><b>+%g</b></td></tr>' % (c, a, d, dif)
        for c, a, d, dif in cambios)
    mo.message_post(body=Markup(
        'Se registró el <b>surtido</b> de la ampliación de esta orden, autorizado por '
        'Mery el 30-sep-2026.<br/><br/>'
        'La orden subió de 3,600 a 3,750 piezas y Mery confirmó que el material extra '
        '<b>ya salió físicamente del almacén</b>; lo que faltaba era registrarlo.<br/><br/>'
        '<table class="table table-sm"><tr><th>Componente</th><th class="text-end">antes</th>'
        '<th class="text-end">ahora</th><th class="text-end">diferencia</th></tr>%s</table>'
        'El vial STBTR02 sube 215 y no 150 porque ya venía con <b>65 pendientes</b> de '
        'antes de la ampliación: tenía 3,535 surtidos de los 3,600 que se pedían.<br/><br/>'
        'La captura de la cantidad surtida corresponde a Almacén. Se hizo desde '
        'Desarrollo por indicación de Mery y queda anotada aquí para que la cifra sea '
        'rastreable.'
    ) % filas)

print('\n=== como queda ===')
mo.invalidate_recordset()
for m in mo.move_raw_ids:
    if m.state == 'cancel':
        continue
    sup = m.amunet_qty_supplied or 0.0
    print('   %-12s pide %8.1f  surtido %8.1f  %s' % (
        m.product_id.default_code or '?', m.product_uom_qty, sup,
        'completo' if abs(sup - m.product_uom_qty) < 0.001 else 'FALTA %.1f' % (m.product_uom_qty - sup)))
print('   la orden puede conciliar: %s' % getattr(mo, 'amunet_can_conciliate', '?'))
env.cr.commit()
