"""Compara config de SPHMC18/56/62 (referencia) vs SPHMC77/78/79 (pendientes)."""
codigos = ['SPHMC18', 'SPHMC56', 'SPHMC62', 'SPHMC77', 'SPHMC78', 'SPHMC79']

for cod in codigos:
    tmpl = env['product.template'].with_context(active_test=False).search([
        ('default_code', '=', cod)], limit=1)
    if not tmpl:
        print(f"{cod}: NO EXISTE")
        continue
    prod = tmpl.product_variant_ids[:1]
    seq = prod.lot_sequence_id
    use_exp = tmpl.use_expiration_date
    tracking = tmpl.tracking
    uom = tmpl.uom_id.name
    seq_prefix = seq.prefix if seq and seq.prefix else '❌ sin secuencia'
    # Lote de ejemplo con sus campos
    lote_ej = env['stock.lot'].search([('product_id', '=', prod.id)], limit=1)
    has_manuf = bool(getattr(lote_ej, 'use_time_constraints', None)) if lote_ej else 'N/A'
    manuf_date = lote_ej.lot_manufacturing_date if lote_ej and hasattr(lote_ej, 'lot_manufacturing_date') else 'N/A'
    removal = lote_ej.removal_date if lote_ej and hasattr(lote_ej, 'removal_date') else 'N/A'
    print(f"[{cod}] tracking={tracking:6s} | exp={str(use_exp):5s} | uom={uom:5s} | seq={seq_prefix}")
    if lote_ej:
        print(f"        lote_ej={lote_ej.name} | fab={manuf_date} | removal={removal}")
