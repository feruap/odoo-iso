# Configurar secuencias de lote automáticas para controles positivos y negativos
# Regla: prefijo = código del producto sin las primeras 3 letras "SPC"
# Ejemplo: SPCPL01 → PL01 → lote generado: PL01062601

controles = env['product.template'].search([
    '|',
    ('default_code', 'like', 'SPCPL'),
    ('default_code', 'like', 'SPCNL'),
], order='default_code')

print("Controles encontrados: %d" % len(controles))
print()

for p in controles:
    prefijo = p.default_code[3:]  # Quitar "SPC" → ej. PL01, NL01
    p.amunet_lot_prefix = prefijo
    print("[%s] %s → prefijo: %s | seq: %s" % (
        p.default_code,
        p.name,
        prefijo,
        p.lot_sequence_id.name if p.lot_sequence_id else 'ERROR: sin secuencia'
    ))

env.cr.commit()
print("\nCOMMIT OK — %d controles configurados" % len(controles))
