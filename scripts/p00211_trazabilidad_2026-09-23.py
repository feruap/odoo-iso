"""P00211: corregir la trazabilidad de una orden que SI se recibio.

APLICADO EN PRODUCCION el 23-sep-2026. Se versiona para dejar constancia de
que se toco y por que (ISO 13485).

El caso: P00211 (Tongzhou, 30-jun-2026) mostraba 0 recibido y tres movimientos
colgados esperando material desde el 1-jul. El material SI habia llegado: entro
el 20-jul por AMP/IN/00200 y AMP/IN/00213, capturadas a mano SIN referencia a la
orden y con el proveedor equivocado (Cangzhou ShengFeng en vez de Tongzhou).

Verificado pieza por pieza contra las 34 lineas de la orden antes de ejecutar:
las cantidades coinciden exactamente y NO hay material duplicado. El -10 que
aparecia en casi todos los productos venia de P00156 y P00157, las ordenes
internas de Amunet a si misma, no de compras reales.

Lo que hace:
  1. Corrige el proveedor de las dos recepciones y las liga a P00211.
  2. Aclara en AMP/IN/00344 que su nota de cancelacion senalaba la recepcion
     equivocada (decia AMP/IN/00346, que no fue).
  3. Cancela los tres movimientos colgados y BLOQUEA la orden (no se cancela:
     la compra si se hizo y si llego).

No mueve ni una pieza de inventario: se comprobo comparando existencias antes y
despues (fotos en /home/agentia-odoo/foto_p00211_*.txt).
"""

Pick = env['stock.picking']
tongzhou = env['res.partner'].search([('name','ilike','Tongzhou')], limit=1)
assert tongzhou, 'no encuentro a Tongzhou'
print('Proveedor correcto: %s (id=%s)' % (tongzhou.name, tongzhou.id))

# ---- 1. corregir proveedor y ligar a P00211 las dos recepciones del 20-jul ----
print('\n--- 1. recepciones del 20-jul ---')
for nombre in ('AMP/IN/00200', 'AMP/IN/00213'):
    p = Pick.search([('name','=',nombre)], limit=1)
    antes_prov = p.partner_id.name
    antes_orig = p.origin or '(vacio)'
    p.sudo().write({'partner_id': tongzhou.id, 'origin': 'P00211'})
    p.message_post(body=(
        'Correccion de trazabilidad 23-sep-2026: esta recepcion ingreso el '
        'material de la orden <b>P00211</b> (Tongzhou, 30-jun-2026), pero se '
        'habia capturado a mano sin referencia a la orden y con el proveedor '
        '<b>%s</b>. Se corrige el proveedor a %s y se liga a P00211. '
        'Verificado pieza por pieza contra las lineas de la orden; no hay '
        'material duplicado.'
    ) % (antes_prov, tongzhou.name))
    print('  %s: proveedor %r -> %r | origen %r -> %r' % (
        nombre, antes_prov, p.partner_id.name, antes_orig, p.origin))

# ---- 2. aclarar la nota de la cancelacion ----
print('\n--- 2. aclaracion en AMP/IN/00344 ---')
p344 = Pick.search([('name','=','AMP/IN/00344')], limit=1)
p344.message_post(body=(
    'Aclaracion 23-sep-2026: la cancelacion fue correcta, pero el motivo '
    'asentado el 22-sep senalaba la recepcion equivocada. El material de '
    'P00211 NO entro por AMP/IN/00346 (P00213): entro el <b>20-jul-2026</b> '
    'por <b>AMP/IN/00200</b> y <b>AMP/IN/00213</b>, capturadas a mano sin '
    'referencia a la orden. Verificado pieza por pieza: las cantidades '
    'coinciden exactamente con las lineas de P00211.'
))
print('  nota publicada (estado sigue: %s)' % p344.state)

# ---- 3. cancelar los movimientos colgados y cerrar la orden ----
print('\n--- 3. movimientos colgados ---')
for nombre in ('AMP/STOR/00118', 'AMP/QC/00399', 'AMP/OUT/00071'):
    p = Pick.search([('name','=',nombre)], limit=1)
    if not p: print('  %s no existe' % nombre); continue
    if p.state in ('done','cancel'):
        print('  %s ya estaba en %s' % (nombre, p.state)); continue
    p.message_post(body=(
        'Cancelado 23-sep-2026: esperaba material de P00211 que ya entro el '
        '20-jul por AMP/IN/00200 y AMP/IN/00213. No queda nada por recibir '
        'por esta via.'
    ))
    p.action_cancel()
    print('  %s -> %s' % (nombre, p.state))

print('\n--- orden P00211 ---')
po = env['purchase.order'].search([('name','=','P00211')], limit=1)
po.message_post(body=(
    'Cierre 23-sep-2026: el material de esta orden <b>ya se recibio completo</b>. '
    'Entro el 20-jul-2026 por AMP/IN/00200 y AMP/IN/00213, capturadas a mano '
    'sin referencia a la orden y con proveedor equivocado (ya corregido). Por '
    'eso la orden mostraba 0 recibido. Verificado pieza por pieza contra las 34 '
    'lineas; no hay material duplicado. Nada que reclamar a Tongzhou. Los tres '
    'movimientos que esperaban material (AMP/STOR/00118, AMP/QC/00399, '
    'AMP/OUT/00071) se cancelaron.'
))
antes = (po.state, po.locked)
po.button_lock()
print("  estado %r -> %r (bloqueada para que no espere mas recepciones)" % (antes, (po.state, po.locked)))
env.cr.commit()
print('\nOK: cambios guardados.')
