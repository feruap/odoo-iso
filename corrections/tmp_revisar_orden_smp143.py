"""
Solo lectura: revisa la orden SMP/26/00143 y sus movimientos de STESP01.
"""
# Buscar el picking por nombre
picking = env['stock.picking'].search([('name', '=', 'SMP/26/00143')], limit=1)
if not picking:
    print("Orden SMP/26/00143 no encontrada")
else:
    print(f"Orden  : {picking.name}")
    print(f"Tipo   : {picking.picking_type_id.name}")
    print(f"Estado : {picking.state}")
    print(f"Fecha  : {picking.date_done or picking.scheduled_date}")
    print(f"Origen : {picking.origin or '-'}")
    print()

    # Líneas de movimiento
    print("Movimientos (stock.move):")
    for m in picking.move_ids:
        print(f"  {m.product_id.default_code:12s} {m.product_id.name:40s} | "
              f"demanda={m.product_uom_qty} | hecho={m.quantity_done} | estado={m.state}")

    print()
    print("Líneas detalle (stock.move.line):")
    for ml in picking.move_line_ids:
        lot_name = ml.lot_id.name if ml.lot_id else 'SIN LOTE'
        qty = getattr(ml, 'qty_done', None) or getattr(ml, 'quantity', None)
        print(f"  {ml.product_id.default_code:12s} | lote={lot_name:20s} | "
              f"qty={qty} | {ml.location_id.complete_name} → {ml.location_dest_id.complete_name} | estado={ml.state}")
