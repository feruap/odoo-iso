"""
Genera lotes automáticos para las 5 hojas de AMP/IN/00159 usando
las secuencias Amunet de cada producto.

Autorizado por: Karla Fernanda Palma Ramos (almacen.mp@amunet.com.mx)
Fecha: 2026-07-29
"""
picking = env['stock.picking'].search([('name', '=', 'AMP/IN/00159')], limit=1)
print(f"Picking: {picking.name} | estado={picking.state}\n")

for ml in picking.move_line_ids:
    if ml.lot_id:
        print(f"  [{ml.product_id.default_code}] ya tiene lote: {ml.lot_id.name}, omitido")
        continue

    prod = ml.product_id
    seq = prod.lot_sequence_id
    if not seq or not seq.prefix:
        print(f"  [{prod.default_code}] ⚠️  sin secuencia Amunet, omitido")
        continue

    # Generar nombre con la secuencia
    lot_name = seq.next_by_id()

    # Crear el lote
    lote = env['stock.lot'].create({
        'name': lot_name,
        'product_id': prod.id,
        'company_id': 1,
    })

    ml.sudo().write({'lot_id': lote.id})
    print(f"  ✅ [{prod.default_code}] → lote {lot_name}")

env.cr.commit()
print("\n✓ Lotes generados — abre la recepción, agrega fechas y valida")
