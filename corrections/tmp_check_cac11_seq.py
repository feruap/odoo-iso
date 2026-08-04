"""Solo lectura: verifica configuración de lotes de CAC11 en producción."""
tmpl = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'CAC11')], limit=1)
if not tmpl:
    print("CAC11 no encontrado")
else:
    prod = tmpl.product_variant_ids[:1]
    seq = prod.lot_sequence_id
    print(f"Producto : {tmpl.name} ({tmpl.default_code})")
    print(f"Tracking : {tmpl.tracking}")
    print(f"Secuencia: {seq.name if seq else '❌ SIN SECUENCIA (lote genérico)'}")
    if seq:
        print(f"  Código : {seq.code}")
        print(f"  Prefijo: {seq.prefix}")
        print(f"  Padding: {seq.padding}")
    lotes = env['stock.lot'].search([('product_id', '=', prod.id)])
    print(f"Lotes existentes: {len(lotes)}")
    for l in lotes:
        print(f"  {l.name}")
