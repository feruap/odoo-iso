"""
Elimina la línea de SPHMC77 de la recepción AMP/IN/00159 (no llegó).
La recepción está en estado 'assigned'.

Autorizado por: Karla Fernanda Palma Ramos (almacen.mp@amunet.com.mx)
Fecha: 2026-07-29
"""
picking = env['stock.picking'].search([('name', '=', 'AMP/IN/00159')], limit=1)
if not picking:
    print("ERROR: AMP/IN/00159 no encontrada")
else:
    print(f"Picking: {picking.name} | estado={picking.state}\n")

    # Buscar la línea de SPHMC77
    move = picking.move_ids.filtered(
        lambda m: m.product_id.default_code == 'SPHMC77')
    move_line = picking.move_line_ids.filtered(
        lambda ml: ml.product_id.default_code == 'SPHMC77')

    if not move:
        print("⚠️  SPHMC77 no encontrada en esta recepción")
    else:
        nombre = move[0].product_id.name
        move_line.sudo().unlink()
        move.sudo().write({'state': 'cancel'})
        move.sudo().unlink()
        env.cr.commit()
        print(f"✅ Línea eliminada: SPHMC77 — {nombre}")
        print(f"   Quedan {len(picking.move_ids)} líneas en la recepción")
