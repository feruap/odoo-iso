"""Solo lectura: verifica secuencia de lotes de MPCAC11."""
tmpl = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'MPCAC11')], limit=1)
prod = tmpl.product_variant_ids[:1]
seq = prod.lot_sequence_id
print(f"Producto : {tmpl.name} ({tmpl.default_code})")
print(f"Tracking : {tmpl.tracking}")
print(f"Secuencia: {seq.name if seq else '❌ SIN SECUENCIA — entrará con lote genérico'}")
if seq:
    print(f"  Prefijo: {seq.prefix}")
    print(f"  Código : {seq.code}")

# Comparar con otro cartucho que sí tenga secuencia, ej. MPCAC03
tmpl3 = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'MPCAC03')], limit=1)
if tmpl3:
    prod3 = tmpl3.product_variant_ids[:1]
    seq3 = prod3.lot_sequence_id
    print(f"\nReferencia MPCAC03: secuencia = {seq3.prefix if seq3 else 'SIN SECUENCIA'}")
