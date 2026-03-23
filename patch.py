picking = env['stock.picking'].browse(542)
qc = picking.amunet_disposition_qc_id
print(f"Fixing picking {picking.name}")
if qc:
    qty_total = qc.original_qty_received or qc.lot_qty_available
    qty_to_stock = max(0.0, qty_total - (qc.qty_sampling or 0.0) + (qc.qty_to_return or 0.0))
    qty_product_uom = qc._convert_qty_to_product_uom(qty_to_stock, qc.sampling_uom_id)
    for move in picking.move_ids:
        move_line = picking.move_line_ids.filtered(lambda ml: ml.move_id == move and ml.product_id == qc.product_id)
        if not move_line:
            env['stock.move.line'].create({
                'picking_id': picking.id,
                'move_id': move.id,
                'product_id': qc.product_id.id,
                'product_uom_id': qc.product_id.uom_id.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'lot_id': qc.lot_id.id if qc.lot_id else False,
                'quantity': qty_product_uom,
                'company_id': picking.company_id.id,
            })
            print("Move line created")
        else:
            move_line.write({'lot_id': qc.lot_id.id if qc.lot_id else False, 'quantity': qty_product_uom})
            print("Move line updated")
env.cr.commit()
