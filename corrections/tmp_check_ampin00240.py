"""Solo lectura: revisa recepción AMP/IN/00240 y sus lotes."""
picking = env['stock.picking'].search([('name', '=', 'AMP/IN/00240')], limit=1)
if not picking:
    print("No encontrada")
else:
    print(f"Picking : {picking.name} | estado={picking.state}")
    print(f"Fecha   : {picking.date_done or picking.scheduled_date}")
    print()
    for ml in picking.move_line_ids:
        lot_name = ml.lot_id.name if ml.lot_id else 'SIN LOTE'
        qty = getattr(ml, 'qty_done', None) or getattr(ml, 'quantity', None)
        print(f"  {ml.product_id.default_code:10s} | lote={lot_name} | qty={qty} | "
              f"{ml.location_dest_id.complete_name} | estado={ml.state}")
        if ml.lot_id:
            print(f"    lot_id={ml.lot_id.id} | nombre actual: '{ml.lot_id.name}'")
