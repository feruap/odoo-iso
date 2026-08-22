picking = env['stock.picking'].browse(994)
print(f"Recepción: {picking.name} | estado: {picking.state}")
for line in picking.move_line_ids:
    print(f"  Producto: {line.product_id.default_code} | lot_name={line.lot_name} | lot_id={line.lot_id.name if line.lot_id else None}")

# Limpiar lot_name para que se regenere con la nueva secuencia
for line in picking.move_line_ids.filtered(lambda l: not l.lot_id):
    line.sudo().write({'lot_name': False})

# Regenerar con la nueva secuencia
for move in picking.move_ids:
    prod = move.product_id
    seq = prod.lot_sequence_id
    print(f"\nSecuencia actual: {seq.code if seq else 'NINGUNA'} | prefix={seq.prefix if seq else '-'}")
    if seq and seq.code.startswith('amunet.lot.'):
        nuevos = prod._amunet_next_lot_names(1)
        print(f"Nuevo lote: {nuevos}")
        for line in move.move_line_ids:
            line.sudo().write({'lot_name': nuevos[0]})

env.cr.commit()
print("\n✓ Lote actualizado")
