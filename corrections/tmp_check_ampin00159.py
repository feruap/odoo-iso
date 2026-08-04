"""Solo lectura: revisa recepción AMP/IN/00159."""
picking = env['stock.picking'].search([('name', '=', 'AMP/IN/00159')], limit=1)
if not picking:
    print("No encontrada")
else:
    print(f"Picking : {picking.name} | estado={picking.state}")
    print(f"Fecha   : {picking.date_done or picking.scheduled_date}")
    print()
    for ml in picking.move_line_ids:
        lot_name = ml.lot_id.name if ml.lot_id else 'SIN LOTE'
        qty = getattr(ml, 'qty_done', None) or getattr(ml, 'quantity', None)
        print(f"  [{ml.product_id.default_code}] {ml.product_id.name}")
        print(f"    lote={lot_name} | qty={qty} | uom={ml.product_uom_id.name}")
        print(f"    destino={ml.location_dest_id.complete_name} | estado={ml.state}")
    print()
    for mv in picking.move_ids:
        print(f"  move: [{mv.product_id.default_code}] qty_demanda={mv.product_uom_qty} "
              f"| qty_hecho={mv.quantity_done} | uom={mv.product_uom.name} | estado={mv.state}")
