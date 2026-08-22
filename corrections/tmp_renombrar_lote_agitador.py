picking = env['stock.picking'].browse(994)
for line in picking.move_line_ids:
    lote = line.lot_id
    if lote and lote.name == '0000001' and line.product_id.default_code == 'EQAMC01':
        print(f"Lote actual: {lote.name} (id={lote.id})")
        lote.sudo().write({'name': 'AMC01072601'})
        line.sudo().write({'lot_name': 'AMC01072601'})
        print(f"Lote renombrado a: {lote.name}")
env.cr.commit()
print("✓ Listo")
