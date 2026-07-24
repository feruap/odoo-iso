# Libera el lote CAR39072601 (MPCAR39, Cartucho Dimero D): aprobado en
# QC/2026/00020 y ya en AMP/Existencias, pero quedo con release_state=pending
# (el hook _finalize_after_reception no libera el lote -> se veia "en cuarentena").
# Se libera con _action_release_lot (snapshot DHR). Autorizado por Fernando 2026-07-21.
lot = env['stock.lot'].sudo().search([('name', '=', 'CAR39072601')], limit=1)
assert lot, 'no existe el lote CAR39072601'
print('lote:', lot.name, '| estado antes:', lot.amunet_lot_release_state)
if lot.amunet_lot_release_state == 'released':
    print('ya estaba liberado, nada que hacer')
else:
    blockers = lot._get_lot_release_blockers()
    if blockers:
        print('BLOQUEOS:', blockers)
    else:
        lot._action_release_lot(notes='Liberacion manual: recepcion AMP/IN/00218 ya validada, material en Existencias')
        env.cr.commit()
        print('estado despues:', lot.amunet_lot_release_state)
