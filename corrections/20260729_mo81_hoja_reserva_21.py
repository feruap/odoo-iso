# Ajusta la MO 81 (0726/01/CAL) tras el cambio de BoM a 0.3: la reserva y el
# surtido (amunet_qty_supplied) de SPHMC55 pasan de 28 -> 21, liberando 7 al
# stock. Autorizado por Fernando 2026-07-29.
mo=env['mrp.production'].sudo().browse(81)
move=mo.move_raw_ids.filtered(lambda m: m.product_id.default_code=='SPHMC55')
print('antes: quantity=%s supplied=%s move_lines=%s'%(move.quantity, move.amunet_qty_supplied, move.move_line_ids.mapped('quantity')))
# reducir la reserva del move_line a 21
mls=move.move_line_ids
if len(mls)==1:
    mls.quantity=21.0
else:
    # dejar 21 en total
    rest=21.0
    for ml in mls:
        take=min(rest, ml.quantity); ml.quantity=take; rest-=take
if 'amunet_qty_supplied' in move._fields:
    move.amunet_qty_supplied=21.0
env.cr.commit()
move=env['mrp.production'].sudo().browse(81).move_raw_ids.filtered(lambda m: m.product_id.default_code=='SPHMC55')
print('despues: demanda=%s quantity=%s supplied=%s reservado=%s'%(move.product_uom_qty, move.quantity, move.amunet_qty_supplied, move.move_line_ids.mapped('quantity')))
print('LISTO')
