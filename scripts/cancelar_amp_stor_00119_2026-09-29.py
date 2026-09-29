"""Cancela AMP/STOR/00119: pide 8,970 combos que nunca llegaron.

Autorizado por Mery el 29-sep-2026, con la revision de Karla del mismo dia:
"Ese material nunca llego en esa cantidad. Las entradas reales fueron julio 1,680
pzas y agosto dos de 2,100 cada una, total real 5,880. Los 8,970 no tienen respaldo
en ninguna recepcion real. Procede a cancelar ese documento."

LO QUE CONFIRMA EL SISTEMA:

    AMP/STOR/00119   pide 8,970 de D000-4055, de AMP/Existencias a Control de calidad
                     estado: EN ESPERA, nada hecho

    recepciones reales de D000-4055:
        AMP/IN/00279   5-ago    30 combos
        AMP/IN/00346  28-ago    30 combos

    existencia hoy:  30 en Control de calidad, y CERO en AMP/Existencias

Los 30 del sistema son COMBOS y las 2,100 pzas de Karla son las pruebas que trae cada
recepcion (30 x 70): las dos cuentas hablan de lo mismo en distinta unidad. Lo que no
cuadra con nada es el 8,970 del documento.

Y por eso esta en espera: pide mover casi nueve mil de una ubicacion donde no hay una
sola pieza. Nunca se iba a poder validar.

Idempotente.
"""
from markupsafe import Markup

Pick = env['stock.picking'].sudo()
p = Pick.search([('name', '=', 'AMP/STOR/00119')], limit=1)
if not p:
    print('[ojo] no existe AMP/STOR/00119')
elif p.state == 'cancel':
    print('[ya] AMP/STOR/00119 ya esta cancelado')
elif p.state == 'done':
    print('[OJO] AMP/STOR/00119 esta VALIDADO: no se cancela sin revisar')
else:
    for m in p.move_ids:
        print('   pide %g %s de %s' % (m.product_uom_qty, m.product_id.default_code,
                                       m.location_id.complete_name))
    p.action_cancel()
    p.invalidate_recordset()
    print('[ok] AMP/STOR/00119 cancelado (estado %s)' % p.state)
    p.message_post(body=Markup(
        'Cancelado el 29-sep-2026, autorizado por Mery con la revision de Karla.'
        '<br/><br/>Pedia mover <b>8,970</b> combos D000-4055 desde AMP/Existencias, '
        'y esa cantidad <b>nunca llego</b>. Las recepciones reales son dos de 30 '
        'combos cada una -- AMP/IN/00279 del 5-ago y AMP/IN/00346 del 28-ago --, que '
        'en piezas son las 2,100 + 2,100 que conto Almacen, mas 1,680 de julio: 5,880 '
        'en total. El 8,970 no corresponde a ninguna recepcion.<br/><br/>'
        'Ademas estaba EN ESPERA porque pedia mover material de una ubicacion donde no '
        'hay una sola pieza: en AMP/Existencias hay cero de este combo, y las 30 que '
        'existen estan en Control de calidad. Nunca se iba a poder validar.'))

print('\n=== como queda ===')
p2 = Pick.search([('name', '=', 'AMP/STOR/00119')], limit=1)
if p2:
    print('   AMP/STOR/00119: %s' % p2.state)
pp = env['product.product'].sudo().search([('default_code', '=', 'D000-4055')], limit=1)
for q in env['stock.quant'].sudo().search([('product_id', '=', pp.id),
                                           ('location_id.usage', '=', 'internal')]):
    if q.quantity:
        print('   existencia: %g en %s' % (q.quantity, q.location_id.complete_name))
otros = Pick.search([('state', 'not in', ('done', 'cancel')),
                     ('move_ids.product_id', '=', pp.id)])
print('   otros documentos abiertos de este combo: %s' % (otros.mapped('name') or 'ninguno'))
env.cr.commit()
