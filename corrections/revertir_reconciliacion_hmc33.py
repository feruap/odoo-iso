# Revierte la reconciliacion de HMC33072601: Calidad va a capturar el analisis
# completo en Odoo, asi que el lote debe volver a su estado original (cuarentena,
# analisis disponible en borrador).
#  1. Traslado interno AMP/Existencias -> Control de calidad (60 cm).
#  2. amunet_lot_release_state -> 'pending' (limpiar campos de liberacion).
#  3. Des-archivar el analisis QC/2026/00021 (vuelve a borrador para que Calidad lo haga).
# Autorizado por Fernando 2026-07-27.
from markupsafe import Markup
lot = env['stock.lot'].sudo().browse(1941)
assert lot.name == 'HMC33072601', 'lote incorrecto'
CC = env['stock.location'].browse(7); EXIST = env['stock.location'].browse(5)
ptype = env['stock.picking.type'].sudo().search([('code', '=', 'internal'), ('warehouse_id.code', '=', 'AMP')], limit=1)

# 1) regresar de Existencias -> Control de calidad
env.cr.execute("SELECT sum(quantity) FROM stock_quant WHERE lot_id=%s AND location_id=%s", (lot.id, EXIST.id))
qty = env.cr.fetchone()[0] or 0.0
print('En Existencias:', qty)
if qty > 0:
    pick = env['stock.picking'].sudo().create({
        'picking_type_id': ptype.id, 'location_id': EXIST.id, 'location_dest_id': CC.id,
        'origin': 'Reversa reconciliacion HMC33072601 (Calidad capturara analisis en Odoo)',
        'move_ids': [(0, 0, {'product_id': lot.product_id.id, 'product_uom_qty': qty,
            'product_uom': lot.product_id.uom_id.id, 'location_id': EXIST.id, 'location_dest_id': CC.id})]})
    pick.action_confirm(); pick.action_assign()
    if pick.move_line_ids:
        for ml in pick.move_line_ids:
            ml.lot_id = lot.id; ml.quantity = qty
    else:
        env['stock.move.line'].create({'picking_id': pick.id, 'move_id': pick.move_ids[0].id,
            'product_id': lot.product_id.id, 'product_uom_id': lot.product_id.uom_id.id,
            'location_id': EXIST.id, 'location_dest_id': CC.id, 'lot_id': lot.id, 'quantity': qty})
    pick.with_context(skip_backorder=True).button_validate()
    print('Traslado:', pick.name, pick.state)

# 2) release_state -> pending (limpiar liberacion)
lot.with_context(skip_lot_release_lock=True).write({
    'amunet_lot_release_state': 'pending',
    'amunet_lot_release_notes': False,
    'amunet_lot_released_by_id': False,
    'amunet_lot_released_date': False,
    'amunet_lot_release_quality_check_id': False,
    'amunet_lot_release_snapshot': False,
    'amunet_lot_release_hash': False,
})
lot.message_post(body=Markup('Reversa de reconciliacion: Calidad capturara el analisis completo en Odoo. Lote regresado a cuarentena y liberacion en pendiente.'))

# 3) des-archivar la QC borrador
qc = env['amunet.quality.check'].sudo().with_context(active_test=False).search([('lot_id', '=', lot.id)], limit=1)
if qc:
    qc.active = True
    qc.message_post(body=Markup('Analisis reactivado: Calidad capturara el analisis en Odoo (reversa de reconciliacion).'))
    print('QC reactivada:', qc.name, '| state:', qc.state)

env.cr.commit()
l2 = env['stock.lot'].sudo().browse(1941)
print('release_state:', l2.amunet_lot_release_state)
env.cr.execute("SELECT sl.complete_name, sq.quantity FROM stock_quant sq JOIN stock_location sl ON sl.id=sq.location_id WHERE sq.lot_id=1941 AND sq.quantity<>0 AND sl.usage='internal'")
print('ubicacion:', env.cr.fetchall())
print('LISTO')
