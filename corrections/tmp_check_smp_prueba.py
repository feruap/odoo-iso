"""Revisa estado de SMP/26/00159 y SMP/26/00160."""
for nombre in ['SMP/26/00159', 'SMP/26/00160']:
    # Buscar en stock.picking por origen
    picks = env['stock.picking'].search([('origin','=',nombre)])
    print(f"\n=== {nombre} ===")
    for p in picks:
        print(f"  Transferencia: {p.name} | tipo={p.picking_type_id.name} | estado={p.state}")
        for ml in p.move_line_ids:
            qty = getattr(ml, 'qty_done', None) or getattr(ml, 'quantity', None) or 0
            lot = ml.lot_id.name if ml.lot_id else 'sin lote'
            print(f"    [{ml.product_id.default_code}] {ml.product_id.name} | lote={lot} | qty={qty} | estado={ml.state}")
    # También buscar el SMP directamente
    try:
        smp = env['amunet.solicitud.material'].search([('name','=',nombre)], limit=1)
        if smp:
            print(f"  SMP estado: {smp.state}")
    except:
        pass
