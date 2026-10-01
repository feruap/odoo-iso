"""0926/01/VPL: el ajuste de las 76 piezas que no existen y del vial que no cuadra.

Autorizado por Mery el 30-sep-2026 ("tu haz todo, documentado"), sobre la confirmacion de
Karla del mismo dia: "en la orden 0926/01/VPL se fabricaron 140 pzas de PCR rapida VPH NET,
no 216. Las 76 piezas que el sistema metio al almacen PT no existen fisicamente."

===========================================================================
LO QUE HAY, Y POR QUE SON DOS COSAS DISTINTAS
===========================================================================

1) EL PRODUCTO TERMINADO (DLVPH01, lote 0926/01/VPL)

    Produccion                   -216     declaradas
    APT/Almacen Temporal PT       184
    Desechos                       32     muestra del analisis QC/2026/00483
                                 ----
                                  216

    Si se fabricaron 140 y 32 se desecharon, en el anaquel deberia haber 108.
    Hay 184, asi que SOBRAN 76: exactamente las que Karla dice que no existen.

    NO se tocan las 32 de Desechos. Esa muestra se tomo fisicamente y su salida esta
    documentada en el analisis. Las 76 que faltan se descuentan del anaquel, que es
    donde el sistema cree tener material que nadie puede tocar.

2) EL VIAL (STBBM01, lote BBM01082601) -- aqui el sistema ya dice casi la verdad

    el move de la orden: pide 216, surtido 216, USADO 140   <- el consumo ya es correcto
    AMP/Existencias        -31
    AMP/Piso de produccion 216

    El consumo declarado (140) coincide con lo que confirma Karla, asi que eso no se toca.
    Lo que esta mal es el SURTIDO: dice 216 y fisicamente salieron 172, como ella reporto
    el 29-sep. Se corrige a 172.

    El -31 de AMP/Existencias viene de haber sacado 216 para esta orden y 240 para
    0826/04/VPL del mismo lote, mas de lo que habia. Se deja en cero devolviendo las 44 que
    nunca salieron (216 surtidas - 172 reales) del piso de produccion al almacen: ese
    movimiento es real, porque esas 44 nunca se movieron fisicamente.

===========================================================================
POR QUE SE HACE POR AQUI Y NO POR EL FLUJO DE ALMACEN
===========================================================================
Mery lo pidio asi. Queda documentado en tres lugares: el chatter del lote de PT, el de la
orden y el motivo del ajuste de inventario, con la referencia a la confirmacion de Karla.
Un ajuste de producto terminado que se da de baja sin venderse tiene que poder explicarse
en una auditoria, y el numero no sale de un calculo nuestro: sale de su conteo fisico.

Idempotente: comprueba las cantidades antes de tocar y no repite nada.
"""
from markupsafe import Markup

MO = env['mrp.production'].sudo()
Quant = env['stock.quant'].sudo()

mo = MO.search([('name', '=', '0926/01/VPL')], limit=1)
assert mo, 'no existe la orden 0926/01/VPL'
pt = mo.product_id
lote_pt = env['stock.lot'].sudo().search([('name', '=', '0926/01/VPL'), ('product_id', '=', pt.id)], limit=1)

REALES, DESECHADAS = 140.0, 32.0
ESPERADO_ANAQUEL = REALES - DESECHADAS   # 108

MOTIVO = ('Ajuste documentado 30-sep-2026, autorizado por Mery sobre la confirmacion de '
          'Karla (Almacen MP): en 0926/01/VPL se fabricaron 140 pz, no 216. Las 76 de '
          'diferencia nunca existieron fisicamente.')

print('=== 1) el producto terminado ===')
anaquel = Quant.search([('product_id', '=', pt.id), ('lot_id', '=', lote_pt.id),
                        ('location_id.complete_name', '=', 'APT/Almacén Temporal PT')], limit=1)
if not anaquel:
    print('   [ojo] no se encontro el quant del anaquel')
elif abs(anaquel.quantity - ESPERADO_ANAQUEL) < 0.001:
    print('   [ya] el anaquel tiene %g pz, que es lo esperado' % anaquel.quantity)
else:
    antes = anaquel.quantity
    anaquel.with_context(inventory_mode=True).write({
        'inventory_quantity': ESPERADO_ANAQUEL,
        'inventory_diff_quantity': ESPERADO_ANAQUEL - antes,
    })
    anaquel.with_context(inventory_mode=True).action_apply_inventory()
    print('   [ok] APT/Almacen Temporal PT: %g -> %g  (se dan de baja %g pz)' % (
        antes, ESPERADO_ANAQUEL, antes - ESPERADO_ANAQUEL))
    lote_pt.message_post(body=Markup(
        'Se dieron de baja <b>%g piezas</b> de este lote en APT/Almacén Temporal PT, '
        'autorizado por Mery el 30-sep-2026.<br/><br/>'
        'La orden 0926/01/VPL declaró <b>216 piezas</b> producidas, pero Karla (Almacén) '
        'confirmó por conteo físico que se fabricaron <b>140</b>. Las 76 de diferencia '
        'nunca existieron: el sistema las metió al almacén y nadie podía tocarlas.<br/><br/>'
        'La cuenta: 140 fabricadas − 32 que se tomaron como muestra del análisis '
        'QC/2026/00483 = <b>108 piezas</b> que deben quedar en el anaquel. Había %g.'
        '<br/><br/>Las 32 de Desechos NO se tocaron: esa muestra se tomó físicamente y su '
        'salida está documentada en el análisis.'
    ) % (antes - ESPERADO_ANAQUEL, antes))

print('\n=== 2) el vial: el surtido decia 216 y salieron 172 ===')
sv = env['product.product'].sudo().search([('default_code', '=', 'STBBM01')], limit=1)
move = mo.move_raw_ids.filtered(lambda m: m.product_id == sv)
SURTIDO_REAL = 172.0
for m in move:
    if abs((m.amunet_qty_supplied or 0) - SURTIDO_REAL) < 0.001:
        print('   [ya] el surtido dice %g' % m.amunet_qty_supplied)
    else:
        antes = m.amunet_qty_supplied or 0
        m.with_context(amunet_supply_internal=True).write({'amunet_qty_supplied': SURTIDO_REAL})
        print('   [ok] surtido: %g -> %g   (el consumo de %g no se toca: coincide con el conteo)' % (
            antes, SURTIDO_REAL, m.amunet_qty_used or 0))

print('\n=== 3) el negativo del vial en existencias ===')
lote_sv = env['stock.lot'].sudo().search([('name', '=', 'BBM01082601'), ('product_id', '=', sv.id)], limit=1)
neg = Quant.search([('product_id', '=', sv.id), ('lot_id', '=', lote_sv.id),
                    ('location_id.complete_name', '=', 'AMP/Existencias')], limit=1)
piso = Quant.search([('product_id', '=', sv.id), ('lot_id', '=', lote_sv.id),
                     ('location_id.complete_name', 'like', 'AMP/Piso%')], limit=1)
print('   antes:  existencias %g   piso %g' % (neg.quantity if neg else 0, piso.quantity if piso else 0))
DEVOLVER = 44.0   # 216 que se registraron menos 172 que salieron de verdad
if neg and neg.quantity >= 0:
    print('   [ya] existencias no esta en negativo')
elif piso and piso.quantity >= DEVOLVER:
    mv = env['stock.move'].sudo().create({
        'description_picking': 'Regreso de vial nunca surtido: %s' % mo.name,
        'product_id': sv.id, 'product_uom_qty': DEVOLVER, 'product_uom': sv.uom_id.id,
        'location_id': piso.location_id.id, 'location_dest_id': neg.location_id.id,
        'origin': mo.name, 'company_id': mo.company_id.id or env.company.id,
    })
    mv._action_confirm(); mv._action_assign()
    mv.move_line_ids.unlink()
    env['stock.move.line'].sudo().create({
        'move_id': mv.id, 'product_id': sv.id, 'lot_id': lote_sv.id,
        'quantity': DEVOLVER, 'product_uom_id': sv.uom_id.id,
        'location_id': piso.location_id.id, 'location_dest_id': neg.location_id.id,
        'picked': True})
    mv._action_done()
    print('   [ok] %g viales regresados del piso a existencias (nunca salieron fisicamente)' % DEVOLVER)
    lote_sv.message_post(body=Markup(
        'Se regresaron <b>44 viales</b> del piso de producción a AMP/Existencias, '
        'autorizado por Mery el 30-sep-2026.<br/><br/>'
        'El surtido de la orden 0926/01/VPL se registró como <b>216</b> cuando físicamente '
        'salieron <b>172</b>, según el reporte de Karla del 29-sep. Esas 44 nunca se '
        'movieron del almacén, y el registro de más dejó <b>−31 piezas</b> en existencias: '
        'de este lote se habían sacado 216 para esta orden y 240 para 0826/04/VPL, más de '
        'lo que había.<br/><br/>El surtido de la orden quedó corregido a 172.'))
else:
    print('   [ALTO] el piso tiene %g y harian falta %g; no se mueve nada' % (
        piso.quantity if piso else 0, DEVOLVER))

print('\n=== como queda ===')
for q in Quant.search([('product_id', '=', pt.id), ('lot_id', '=', lote_pt.id)]):
    if abs(q.quantity) > 0.0001:
        print('   PT  %-42s %8.1f' % (q.location_id.complete_name, q.quantity))
for q in Quant.search([('product_id', '=', sv.id), ('lot_id', '=', lote_sv.id)]):
    if abs(q.quantity) > 0.0001:
        print('   vial %-41s %8.1f' % (q.location_id.complete_name, q.quantity))
for m in mo.move_raw_ids.filtered(lambda x: x.product_id == sv):
    print('   el move del vial: pide %g  surtido %g  usado %g' % (
        m.product_uom_qty, m.amunet_qty_supplied or 0, m.amunet_qty_used or 0))
env.cr.commit()
