env = env(su=True)

lotes_a_borrar = ['REC02062601', 'REC04122501']

for nombre in lotes_a_borrar:
    lote = env['stock.lot'].search([('name', '=', nombre)], limit=1)
    if not lote:
        print(f"AVISO: lote {nombre} no encontrado, omitiendo.")
        continue

    # Eliminar movimientos de inventario asociados
    quants = env['stock.quant'].search([('lot_id', '=', lote.id)])
    print(f"Lote: {nombre} | Producto: {lote.product_id.default_code} - {lote.product_id.name}")
    print(f"  Quants a eliminar: {len(quants)}")
    quants.sudo().unlink()

    lote.sudo().unlink()
    print(f"  Lote {nombre} eliminado.")

env.cr.commit()
print("Listo.")
