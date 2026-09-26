# Cartucho de Tifoidea MPCAR43, lote CAR43082601. Karla lo reporto atorado.
#
# Que paso: la liberacion AMP/IN/00401 (08-sep) se registro como RECEPCION desde
# Proveedor en vez de traslado interno, asi que en vez de mover el material lo
# duplico: 346 pz fantasma en AMP/Entrada. El sistema las leyo como recepcion
# nueva y genero el picking de calidad AMP/QC/00408, que nunca debio existir.
# Ese defecto ya se corrigio en codigo (commit 2ee9bf3, 22-sep).
#
# Estado antes: Proveedor -696 (deberia ser -350), 346 en AMP/Entrada
# (reservadas por el picking fantasma), 346 en cuarentena, 4 en Desechos,
# CERO en AMP/Existencias.
#
# Se corrige en tres pasos:
#   1. cancelar el picking fantasma AMP/QC/00408
#   2. sacar del inventario las 346 fantasma, con motivo escrito
#   3. mover las 346 REALES de cuarentena a AMP/Existencias
#
# Se usa ajuste de inventario y no 'devolucion al proveedor' porque esas piezas
# nunca existieron: una devolucion diria en el historial que le regresamos
# cartuchos a un proveedor, y eso no ocurrio. Decision de Mery, 23-sep-2026.
MOTIVO = ('Correccion 23-sep-2026: piezas duplicadas por la liberacion '
          'AMP/IN/00401, que se registro como recepcion en vez de traslado '
          'interno. Nunca existieron fisicamente. Pedido por Almacen MP (Karla).')

L = env['stock.lot']; Q = env['stock.quant']; P = env['stock.picking']
lot = L.search([('name', '=', 'CAR43082601')], limit=1)
assert lot, 'No existe el lote'

def foto(t):
    print('%s' % t)
    for q in Q.search([('lot_id', '=', lot.id), ('quantity', '!=', 0)], order='id'):
        print('   %-38s %8s' % (q.location_id.complete_name, q.quantity))

foto('--- ANTES ---')

# 1. cancelar el picking fantasma
pk = P.search([('name', '=', 'AMP/QC/00408')], limit=1)
if pk and pk.state != 'cancel':
    pk.action_cancel()
    pk.message_post(body=MOTIVO)
    print('\n  cancelado AMP/QC/00408 (estaba en %s)' % pk.state)

# 2. sacar las fantasma de AMP/Entrada
entrada = env['stock.location'].search([('complete_name', '=', 'AMP/Entrada')], limit=1)
quants = Q.search([('lot_id', '=', lot.id), ('location_id', '=', entrada.id)])
pz = sum(quants.mapped('quantity'))
if pz:
    quants.with_context(inventory_mode=True).write({
        'inventory_quantity': 0.0,
        'inventory_diff_quantity': -pz,
    })
    quants.with_context(inventory_mode=True).action_apply_inventory()
    print('  ajuste: %s pz fantasma fuera de AMP/Entrada' % pz)

# 3. las REALES de cuarentena a AMP/Existencias
cuarentena = env['stock.location'].search([('complete_name', 'like', 'AMP/Entrada/Control de calidad')], limit=1)
destino = env['stock.location'].search([('complete_name', '=', 'AMP/Existencias')], limit=1)
reales = sum(Q.search([('lot_id', '=', lot.id), ('location_id', '=', cuarentena.id)]).mapped('quantity'))
if reales > 0:
    mv = env['stock.move'].create({
        'product_id': lot.product_id.id, 'product_uom': lot.product_id.uom_id.id,
        'product_uom_qty': reales, 'location_id': cuarentena.id,
        'location_dest_id': destino.id,
        'origin': 'Almacenamiento CAR43082601 (correccion liberacion AMP/IN/00401)',
    })
    mv._action_confirm(); mv.move_line_ids.unlink()
    env['stock.move.line'].create({
        'move_id': mv.id, 'product_id': lot.product_id.id, 'lot_id': lot.id,
        'quantity': reales, 'product_uom_id': lot.product_id.uom_id.id,
        'location_id': cuarentena.id, 'location_dest_id': destino.id,
    })
    mv.picked = True; mv._action_done()
    assert mv.state == 'done', 'El movimiento quedo en %s' % mv.state
    print('  %s pz reales movidas de cuarentena a AMP/Existencias' % reales)

lot.message_post(body=MOTIVO)
env.cr.commit()
foto('\n--- DESPUES ---')
