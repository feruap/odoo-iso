# AMP/IN/00213: cambia el cartucho Mycoplasma placeholder MPCAR73 por el real
# MPCAR32 (autollena lote CAR32...). Luego archiva placeholders MPCAR72-76.
# Autorizado por Fernando 2026-07-20.
picking = env['stock.picking'].search([('name','=','AMP/IN/00213')], limit=1)
assert picking and picking.state=='assigned', 'picking inesperado'
m73 = env['product.product'].search([('default_code','=','MPCAR73')], limit=1)
m32 = env['product.product'].search([('default_code','=','MPCAR32')], limit=1)
move = picking.move_ids.filtered(lambda mv: mv.product_id==m73)
assert len(move)==1, 'no encontre 1 movimiento de MPCAR73'
qty = move.product_uom_qty
src, dest = move.location_id, move.location_dest_id
# eliminar el movimiento del placeholder
move.move_line_ids.unlink()
move.write({'state':'draft'})
move.unlink()
# crear el movimiento del producto real
newmove = env['stock.move'].create({
    'description_picking': m32.display_name, 'picking_id': picking.id,
    'product_id': m32.id, 'product_uom_qty': qty, 'product_uom': m32.uom_id.id,
    'location_id': src.id, 'location_dest_id': dest.id,
})
picking.action_confirm()
picking.action_assign()
env.cr.commit()
for ml in newmove.move_line_ids:
    print('Nueva linea MPCAR32: lot_name=%s qty=%s' % (ml.lot_name, ml.quantity))
# archivar placeholders vacios
ph = env['product.template'].search([('default_code','in',['MPCAR72','MPCAR73','MPCAR74','MPCAR75','MPCAR76'])])
ph.sudo().write({'active': False})
print('Archivados:', ph.mapped('default_code'))
env.cr.commit()
print('COMMIT')
