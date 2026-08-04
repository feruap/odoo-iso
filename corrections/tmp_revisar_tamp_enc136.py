"""
Revisa el picking T/AMP/ENC/00136 y su relación con STESP01 / ESP01072601.
"""
picking = env['stock.picking'].search([('name', '=', 'T/AMP/ENC/00136')], limit=1)
if not picking:
    print("No encontrado")
else:
    print(f"Picking : {picking.name}")
    print(f"Tipo    : {picking.picking_type_id.name}")
    print(f"Estado  : {picking.state}")
    print(f"Origen  : {picking.origin}")
    print(f"Fecha   : {picking.date_done or picking.scheduled_date}")
    print()

    print("Líneas detalle (stock.move.line):")
    for ml in picking.move_line_ids:
        lot_name = ml.lot_id.name if ml.lot_id else 'SIN LOTE'
        qty = getattr(ml, 'qty_done', None) or getattr(ml, 'quantity', None)
        print(f"  {ml.product_id.default_code:12s} | lote={lot_name:20s} | "
              f"qty={qty:6} | {ml.location_id.complete_name} → {ml.location_dest_id.complete_name} | estado={ml.state}")

    print()
    # ¿Hay algo de STESP01 en los quants de la ubicación destino?
    esp = env['product.template'].search([('default_code', '=', 'STESP01')], limit=1)
    if esp:
        prod = esp.product_variant_ids[:1]
        lot = env['stock.lot'].search([('name', '=', 'ESP01072601'), ('product_id', '=', prod.id)], limit=1)
        print(f"Quants de ESP01072601 en TODO el sistema:")
        quants = env['stock.quant'].search([('lot_id', '=', lot.id)])
        for q in quants:
            print(f"  {q.location_id.complete_name:50s}  qty={q.quantity:8.2f}")

        print()
        print("Movimientos de ESP01072601 (stock.move.line):")
        mls = env['stock.move.line'].search([('lot_id', '=', lot.id)], order='date asc')
        for ml in mls:
            qty = getattr(ml, 'qty_done', None) or getattr(ml, 'quantity', None)
            print(f"  {str(ml.date)[:19]} | {ml.state:10s} | "
                  f"{ml.location_id.complete_name:35s} → {ml.location_dest_id.complete_name:35s} | "
                  f"qty={qty} | ref={ml.reference or ml.picking_id.name or '-'}")
