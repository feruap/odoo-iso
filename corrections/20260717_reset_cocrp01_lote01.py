"""
Limpieza de prueba para COCRP01 en staging:
  - Cancela la orden de calidad AMP/QC/00369 (pendiente)
  - Limpia el quant de inventario dejado por la recepción anterior
  - Elimina el lote CRP01072601 para que el próximo intento genere el 01
"""
env = env(su=True)

producto = env['product.product'].search([
    ('product_tmpl_id.default_code', '=', 'COCRP01')
], limit=1)
print(f"Producto: {producto.display_name}")

# 1. Cancelar la orden de calidad pendiente
qc = env['stock.picking'].search([('name', '=', 'AMP/QC/00369')], limit=1)
if qc:
    print(f"Orden QC: {qc.name} | estado: {qc.state}")
    if qc.state not in ('done', 'cancel'):
        qc.action_cancel()
        print(f"  → Cancelada")
    else:
        print(f"  → Ya estaba en {qc.state}, sin cambio")

# 2. Limpiar quants del lote CRP01072601
lote = env['stock.lot'].search([
    ('name', '=', 'CRP01072601'),
    ('product_id', '=', producto.id),
], limit=1)

if lote:
    quants = env['stock.quant'].search([('lot_id', '=', lote.id)])
    print(f"Quants a limpiar: {len(quants)}")
    for q in quants:
        print(f"  ubicación id={q.location_id.id} qty={q.quantity} res={q.reserved_quantity}")
    quants.sudo().unlink()
    print(f"  → Quants eliminados")

    # 3. Eliminar el lote (ahora sin referencias)
    lote_nombre = lote.name
    lote.sudo().unlink()
    print(f"Lote {lote_nombre} eliminado")
else:
    print("Lote CRP01072601 no encontrado")

env.cr.commit()
print("✓ Listo — el próximo intento generará CRP01072601")
