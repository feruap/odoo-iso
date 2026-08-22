p = env['product.template'].with_context(active_test=False).search([
    ('default_code','=','STESP01')], limit=1)
if not p:
    print("No existe en staging")
else:
    prod = p.product_variant_ids[:1]
    seq = prod.lot_sequence_id
    print(f"[{p.default_code}] {p.name}")
    print(f"  tracking={p.tracking}")
    print(f"  secuencia={seq.code if seq else 'NINGUNA (genérica)'}")
    print(f"  categ={p.categ_id.complete_name}")
