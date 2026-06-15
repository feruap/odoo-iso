# Activar rastreo por lote y configurar secuencias para Consumible/EPP y Consumible/Muestra
# Regla: prefijo = código sin las primeras 2 letras "CO"
# Ejemplo: COBDE01 → BDE01 → lote: BDE01062601

cat_ids = [75, 80]  # Consumible/EPP y Consumible/Muestra

productos = env['product.template'].search(
    [('categ_id', 'in', cat_ids)],
    order='default_code'
)

print("Productos a configurar: %d" % len(productos))
print()

for p in productos:
    prefijo = p.default_code[2:]  # Quitar "CO" → ej. BDE01, AVC01
    # 1. Activar rastreo por lote
    p.write({'tracking': 'lot'})
    # 2. Asignar prefijo (crea la secuencia automáticamente)
    p.amunet_lot_prefix = prefijo
    print("[%s] %s → prefijo: %s | seq: %s" % (
        p.default_code,
        p.name,
        prefijo,
        p.lot_sequence_id.name if p.lot_sequence_id else 'ERROR'
    ))

env.cr.commit()
print("\nCOMMIT OK — %d productos configurados" % len(productos))
