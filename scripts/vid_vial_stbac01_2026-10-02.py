# 1026/01/VID: el vial cambia de STBCH01 (con Chem) a STBAC01. (Mery, 2-oct)
# Solo en ESTA orden: el vial no viene del BoM, viene del empaque.
#
# Las dos trampas ya conocidas al cambiar el producto de un move: la linea
# conserva el lote del producto viejo, y _action_assign() no reserva si el
# move esta marcado como surtido (picked).
CTX = {'amunet_supply_internal': True}
mo = env['mrp.production'].browse(167)
viejo = env['product.product'].search([('default_code', '=', 'STBCH01')], limit=1)
nuevo = env['product.product'].search([('default_code', '=', 'STBAC01')], limit=1)
m = mo.move_raw_ids.filtered(lambda x: x.product_id == viejo)
print('antes:', m.product_id.default_code, '| req', m.product_uom_qty,
      '| surtido', m.amunet_qty_supplied,
      '| lote', [l.lot_id.name for l in m.move_line_ids])

surtido = m.amunet_qty_supplied
m.sudo()._do_unreserve()
m.move_line_ids.sudo().unlink()
m.sudo().with_context(**CTX).write({
    'product_id': nuevo.id, 'product_uom': nuevo.uom_id.id,
    'amunet_lot_id': False, 'amunet_qty_supplied': surtido})
m.sudo().picked = False
m.sudo()._action_assign()
m.sudo().picked = True
m.invalidate_recordset()
print('ahora:', m.product_id.default_code, '| req', m.product_uom_qty,
      '| surtido', m.amunet_qty_supplied,
      '| lote', [(l.lot_id.name, l.quantity) for l in m.move_line_ids])

mo.message_post(body=(
    'Cambiado el <b>vial</b>: de STBCH01 (con Chem) a <b>STBAC01</b>, por '
    'indicacion de Mery. Es cambio solo de esta orden: el vial no viene de la '
    'receta sino del empaque.'))
env.cr.commit()

print()
print('=== caducidad del lote que tomo ===')
for l in m.move_line_ids:
    print('   %-13s caduca %s' % (l.lot_id.name,
          l.lot_id.expiration_date.date() if l.lot_id.expiration_date else 'sin fecha'))
print()
print('=== la orden completa ===')
mal = []
for mv in mo.move_raw_ids.sorted(lambda x: x.product_id.default_code or ''):
    for l in mv.move_line_ids:
        if l.lot_id and l.lot_id.product_id != mv.product_id:
            mal.append((mv.product_id.default_code, l.lot_id.name))
    print('   %-9s req %7s  %s' % (mv.product_id.default_code, mv.product_uom_qty,
          [(l.lot_id.name, l.quantity) for l in mv.move_line_ids] or 'SIN LOTE'))
print('lotes cruzados:', mal or 'ninguno')
