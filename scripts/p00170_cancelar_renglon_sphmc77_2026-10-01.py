# -*- coding: utf-8 -*-
"""P00170: cancelar el renglon de SPHMC77 y su recepcion AMP/IN/00257.

EL CASO
Pedido P00170 a Zhejiang Orient Gene (04-jun-2026), 6 hojas maestras. Cinco se
recibieron el 26-jul en AMP/IN/00159. La sexta, SPHMC77 (Hoja Maestra
Transglutaminasa IgA), quedo en AMP/IN/00257 con 120 piezas reservadas desde el
29-jul y nunca llego. Fecha prometida: 04-jul. Tres meses de retraso.

Karla confirmo el 30-sep que fisicamente no llego. Mery autorizo cancelar el
01-oct-2026.

POR QUE SE CANCELAN LAS DOS COSAS JUNTAS
Cancelar solo la recepcion no cancela el renglon del pedido: P00170 se quedaria
esperando un material que nadie va a mandar, y encima se pierde la senal visible
de que falta algo -- la recepcion abierta era justamente esa senal-. Por eso el
01-sep se dejo el caso abierto a proposito en vez de cerrar la recepcion sola.

Las dos acciones, en este orden:
  1. cancelar la recepcion AMP/IN/00257
  2. poner el renglon de SPHMC77 en cantidad CERO

El renglon no se borra: se deja en cero. Borrarlo quitaria del pedido la
constancia de que ese material se pidio y no llego, y el pedido es el documento
que lo prueba.

OJO: poner el renglon en cero cambia el total del pedido. Es el efecto buscado al
cancelar un renglon.

El pedido NO se cancela: sus otras cinco lineas si se recibieron. Se deja en su
estado actual; con el renglon en cero ya no queda nada por recibir.

Idempotente: comprueba el estado antes de cada paso.
"""

MARCA = '[renglon SPHMC77 cancelado 01-oct-2026]'

orden = env['purchase.order'].search([('name', '=', 'P00170')], limit=1)
if not orden:
    raise Exception('no existe P00170')
print('P00170  estado=%s  proveedor=%s' % (orden.state, orden.partner_id.name))

# --- 1) la recepcion ---
recep = env['stock.picking'].search([('name', '=', 'AMP/IN/00257')], limit=1)
if not recep:
    print('  [!] no existe AMP/IN/00257')
elif recep.state == 'cancel':
    print('  AMP/IN/00257 ya estaba cancelada')
else:
    print('  AMP/IN/00257 estado=%s -> cancelando' % recep.state)
    recep.action_cancel()
    print('  AMP/IN/00257 quedo en: %s' % recep.state)

# --- 2) el renglon ---
linea = orden.order_line.filtered(lambda l: l.product_id.default_code == 'SPHMC77')
if not linea:
    print('  [!] no se encontro el renglon de SPHMC77')
else:
    linea.ensure_one()
    print('  renglon SPHMC77: pedido=%s  recibido=%s' % (linea.product_qty, linea.qty_received))
    if linea.qty_received:
        print('  [!] tiene material recibido -- NO SE TOCA, revisar a mano')
    elif linea.product_qty == 0:
        print('  el renglon ya estaba en cero')
    else:
        linea.product_qty = 0
        print('  renglon puesto en cero (no se borra: el pedido es la constancia de que se pidio)')

# --- 3) la constancia escrita ---
NOTA = """%s

<p>Se cancelo el renglon de <b>SPHMC77 (Hoja Maestra Transglutaminasa IgA)</b> y su
recepcion <b>AMP/IN/00257</b>.</p>

<p><b>Motivo:</b> el material nunca llego. La recepcion estuvo con 120 piezas
reservadas desde el 29-jul-2026 y la fecha prometida por el proveedor era el
04-jul-2026: tres meses de retraso sin entrega. Karla (Almacen MP) confirmo el
30-sep-2026 que fisicamente no se recibio.</p>

<p>Los otros cinco renglones de este pedido si se recibieron completos el
26-jul-2026 en AMP/IN/00159, por eso el pedido no se cancela entero.</p>

<p>El renglon se dejo en <b>cantidad cero en lugar de borrarlo</b>: asi el pedido
sigue siendo la constancia de que ese material se pidio y no llego.</p>

<p>Autorizado por Mery el 01-oct-2026. Si Orient Gene confirma despues que lo
envia, se levanta un pedido nuevo.</p>""" % MARCA

for rec, etq in [(orden, 'P00170'), (recep, 'AMP/IN/00257')]:
    if not rec:
        continue
    ya = env['mail.message'].search_count([('model', '=', rec._name), ('res_id', '=', rec.id),
                                           ('body', 'ilike', MARCA)])
    if ya:
        print('  nota ya estaba en %s' % etq)
    else:
        rec.sudo().message_post(body=NOTA)
        print('  nota puesta en %s' % etq)

env.cr.commit()

print('\n=== COMO QUEDO ===')
orden.invalidate_recordset()
print('  P00170 estado: %s' % orden.state)
for l in orden.order_line.sorted(lambda x: x.product_id.default_code or ''):
    print('    %-9s pedido=%-7s recibido=%s' % (l.product_id.default_code, l.product_qty, l.qty_received))
print('  AMP/IN/00257 estado: %s' % (recep.state if recep else '?'))
otras = env['stock.picking'].search([('origin', 'like', '%P00170%')])
for p in otras.sorted('id'):
    print('    %-14s %s' % (p.name, p.state))
print('\nqueda algo por recibir en P00170: %s' % ('SI -- revisar' if any(
    l.product_qty > l.qty_received for l in orden.order_line) else 'no'))
