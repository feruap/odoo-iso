"""
Corrige cantidad de 6 hojas maestras en AMP/IN/00159: 4 cm → 120 cm.
La recepción está en estado 'assigned' (no validada).

Autorizado por: Karla Fernanda Palma Ramos (almacen.mp@amunet.com.mx)
Fecha: 2026-07-29
"""
picking = env['stock.picking'].search([('name', '=', 'AMP/IN/00159')], limit=1)
if not picking:
    print("ERROR: AMP/IN/00159 no encontrada")
else:
    print(f"Picking: {picking.name} | estado={picking.state}\n")
    for ml in picking.move_line_ids:
        codigo = ml.product_id.default_code
        qty_actual = getattr(ml, 'qty_done', None) or getattr(ml, 'quantity', None) or 0
        ml.sudo().write({'quantity': 120.0})
        print(f"  ✅ [{codigo}] {ml.product_id.name[:45]} | {qty_actual} → 120 cm")

    # Actualizar también la demanda en stock.move
    for mv in picking.move_ids:
        mv.sudo().write({'product_uom_qty': 120.0})

    env.cr.commit()
    print("\n✓ Cantidades actualizadas a 120 cm en las 6 líneas")
