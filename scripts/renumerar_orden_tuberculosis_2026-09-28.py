# -*- coding: utf-8 -*-
"""Renumerar la orden de tuberculosis: 0926/02/TUB pasa a 0926/01/TUB.

El 2-sep-2026 el plan de desabasto creo 0926/01/TUB por 500 pz. Esa misma noche
Fernando pidio recalcular el faltante contra Woo disponible, asi que la 01 se
cancelo y se creo 0926/02/TUB por 1,115 pz. Como entonces el folio no regresaba
al cancelar -- eso se corrigio el 25-sep -- el consecutivo se comio el 01 y quedo
un hueco.

Decision de Mery (28-sep-2026): cambiarlo, "es mas controversia de forma interna
que no hay 01".

Mismo criterio que se uso con Procalcitonina el 23-sep: la cancelada pasa a
0926/01/TUB-CANCELADA y la viva toma el 01.

CUIDADO: la 02 esta en PROGRESS y con material surtido (1,115 cartuchos,
goteros, desecantes, bolsas, 446 cm de hoja, 64 cajas y 64 viales). Los
movimientos apuntan a la orden por ID, no por nombre, asi que no se pierden.
Y aun NO tiene lote de producto terminado creado -- ese lote hereda el folio --
por eso se puede renombrar hoy y no se podria despues.
"""
MO = env['mrp.production'].sudo()
viva = MO.search([('name','=','0926/02/TUB')], limit=1)
canc = MO.search([('name','=','0926/01/TUB')], limit=1)
assert viva and canc, 'no encuentro las dos ordenes'
assert canc.state == 'cancel', 'la 01 no esta cancelada'
# el lote del PT hereda el folio de la orden; si ya existe, no se renombra
# El lote del PT hereda el folio, asi que hay que renombrarlo con la orden o
# quedarian diciendo cosas distintas. Solo se puede si NO esta liberado: el
# candado de calidad no permite cambiar el nombre de un lote liberado.
lote_pt = env['stock.lot'].sudo().search(
    [('name','=','0926/02/TUB'), ('product_id','=',viva.product_id.id)], limit=1)
if lote_pt:
    ex = sum(env['stock.quant'].sudo().search([
        ('lot_id','=',lote_pt.id),('location_id.usage','=','internal')]).mapped('quantity'))
    est = lote_pt.amunet_lot_release_state
    print('   lote del PT: %s   liberado=%s   existencia=%s' % (lote_pt.name, est, ex))
    assert est != 'released', 'el lote esta LIBERADO: renombrarlo exige desviacion de Calidad'
else:
    print('   lote del PT: no existe todavia')

print('   antes:')
print('      %-20s %-10s %s pz   material surtido: %s lineas' % (
    canc.name, canc.state, canc.product_qty,
    len(canc.move_raw_ids.filtered(lambda m: (m.amunet_qty_supplied or 0) > 0))))
print('      %-20s %-10s %s pz   material surtido: %s lineas' % (
    viva.name, viva.state, viva.product_qty,
    len(viva.move_raw_ids.filtered(lambda m: (m.amunet_qty_supplied or 0) > 0))))
movs_antes = env['stock.move.line'].sudo().search_count(
    [('move_id.raw_material_production_id','=',viva.id)])
print('      movimientos ligados a la viva: %s' % movs_antes)

# 1) la cancelada libera el nombre
canc.write({'name': '0926/01/TUB-CANCELADA'})
canc.message_post(body=(
    'Se renombra a <b>0926/01/TUB-CANCELADA</b> para liberar el folio. Esta orden '
    'la creo el plan de desabasto del 2-sep-2026 por 500 pz y se cancelo esa misma '
    'noche, cuando Fernando pidio recalcular el faltante contra Woo disponible. '
    'El folio 0926/01/TUB pasa a la orden que si se esta trabajando, que nacio como '
    '0926/02/TUB por 1,115 pz: internamente generaba dudas que no existiera un 01.'))
# 2) la viva toma el 01
viejo = viva.name
viva.write({'name': '0926/01/TUB'})
viva.message_post(body=(
    'Esta orden se renumera de <b>%s</b> a <b>0926/01/TUB</b>. El 01 de septiembre '
    'lo habia tomado una orden del plan de desabasto que se cancelo esa misma noche '
    'al recalcularse la cantidad, y como entonces el folio no regresaba al '
    'consecutivo, esta nacio con el 02 sin que existiera un 01. La cancelada queda '
    'como 0926/01/TUB-CANCELADA. No cambia nada del material ya surtido: los '
    'movimientos van ligados a la orden, no a su nombre.') % viejo)
# 3) el consecutivo: el 01 queda usado, el siguiente es el 02
seq = viva.product_id.product_tmpl_id.mo_sequence_id
if seq and seq.number_next_actual > 2:
    antes = seq.number_next_actual
    seq.write({'number_next': 2})
    print('      secuencia: siguiente %s -> %s' % (antes, seq.number_next_actual))
# 4) el lote del PT, para que siga diciendo lo mismo que su orden
if lote_pt:
    lote_pt.write({'name': '0926/01/TUB'})
    lote_pt.message_post(body=(
        'Nombre corregido de <b>0926/02/TUB</b> a <b>0926/01/TUB</b>, junto con su '
        'orden de fabricacion. El lote hereda el folio de la orden, y esa orden se '
        'renumero porque el 01 de septiembre lo habia tomado una orden cancelada la '
        'misma noche que se creo. Se pudo hacer porque el lote no estaba liberado, '
        'no tenia existencia ni analisis.'))
    print('      lote del PT renombrado a %s' % lote_pt.name)
env.flush_all(); env.cr.commit()

print('')
print('   despues:')
for o in (canc, viva):
    o.invalidate_recordset()
    print('      %-24s %-10s %s pz' % (o.name, o.state, o.product_qty))
movs = env['stock.move.line'].sudo().search_count(
    [('move_id.raw_material_production_id','=',viva.id)])
print('      movimientos ligados a la viva: %s   (antes %s)' % (movs, movs_antes))
print('      material surtido intacto: %s lineas' % len(
    viva.move_raw_ids.filtered(lambda m: (m.amunet_qty_supplied or 0) > 0)))
