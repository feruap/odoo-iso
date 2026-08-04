"""Revisa estado de lotes en AMP/IN/00159 tras marcar por realizar."""
picking = env['stock.picking'].search([('name', '=', 'AMP/IN/00159')], limit=1)
print(f"Picking: {picking.name} | estado={picking.state}\n")

print("Líneas detalle (move.line):")
for ml in picking.move_line_ids:
    lot = ml.lot_id.name if ml.lot_id else '❌ SIN LOTE'
    qty = getattr(ml, 'quantity', None) or getattr(ml, 'qty_done', None) or 0
    prod = ml.product_id
    seq = prod.lot_sequence_id
    print(f"  [{prod.default_code}] lote={lot} | qty={qty} | seq={seq.prefix if seq and seq.prefix else 'sin secuencia'}")
