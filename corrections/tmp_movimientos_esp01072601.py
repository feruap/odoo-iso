"""
Solo lectura: muestra todos los movimientos del lote ESP01072601 en producción.
"""
lot = env['stock.lot'].search([('name', '=', 'ESP01072601')], limit=1)
if not lot:
    print("Lote ESP01072601 no encontrado")
else:
    print(f"Lote   : {lot.name}")
    print(f"Prod   : {lot.product_id.name} ({lot.product_id.default_code})")
    print(f"Qty ON HAND (sistema): {lot.product_qty}")
    print()

    moves = env['stock.move.line'].search(
        [('lot_id', '=', lot.id)], order='date asc'
    )
    print(f"Movimientos (stock.move.line): {len(moves)}")
    for m in moves:
        ref = m.reference or m.move_id.origin or m.picking_id.name or '-'
        print(f"  {str(m.date)[:19]} | estado={m.state:12s} | "
              f"{m.location_id.complete_name:35s} → {m.location_dest_id.complete_name:35s} | "
              f"qty={getattr(m,'qty_done',None) or getattr(m,'quantity',None)} | ref={ref}")

    print()
    quants = env['stock.quant'].search([('lot_id', '=', lot.id)])
    print("Quants actuales:")
    for q in quants:
        print(f"  {q.location_id.complete_name:50s}  qty={q.quantity:8.2f}")
