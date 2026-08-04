"""Solo lectura: verifica configuración de SPHMC77, 78 y 79 para recepción correcta."""
codigos = ['SPHMC77', 'SPHMC78', 'SPHMC79']

for cod in codigos:
    tmpl = env['product.template'].with_context(active_test=False).search([
        ('default_code', '=', cod)], limit=1)
    if not tmpl:
        print(f"{cod}: NO EXISTE")
        continue
    prod = tmpl.product_variant_ids[:1]
    seq = prod.lot_sequence_id
    print(f"[{cod}] {tmpl.name}")
    print(f"  Tracking              : {tmpl.tracking}")
    print(f"  UoM                   : {tmpl.uom_id.name}")
    print(f"  use_expiration_date   : {tmpl.use_expiration_date}")
    print(f"  use_removal_date      : {getattr(tmpl, 'use_removal_date', 'N/A')}")
    print(f"  use_time_constraints  : {getattr(tmpl, 'use_time_constraints', 'N/A')}")
    print(f"  Secuencia Amunet      : {seq.prefix if seq and seq.prefix else '❌ genérica/sin configurar'}")
    # Checar si tiene campo de lote proveedor (factory_lot_id en stock.lot)
    lotes = env['stock.lot'].search([('product_id', '=', prod.id)], limit=1)
    if lotes:
        print(f"  Lote de ejemplo       : {lotes.name} | prov={lotes.factory_lot_id.name if lotes.factory_lot_id else 'sin campo'}")
    print()
