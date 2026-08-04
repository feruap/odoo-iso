"""Verifica si CAR77/78/79 existen y revisa config de cartuchos de referencia."""
# ¿Ya existen?
for cod in ['CAR77', 'CAR78', 'CAR79']:
    t = env['product.template'].with_context(active_test=False).search([
        ('default_code', '=', cod)], limit=1)
    print(f"{cod}: {'✅ ya existe — '+t.name if t else '❌ no existe'}")

print()
# Referencia: cartucho existente
refs = ['MPCAC11', 'MPCAC03', 'MPCAR17']
for cod in refs:
    t = env['product.template'].with_context(active_test=False).search([
        ('default_code', '=', cod)], limit=1)
    if not t:
        continue
    prod = t.product_variant_ids[:1]
    seq = prod.lot_sequence_id
    print(f"[{cod}] {t.name}")
    print(f"  categ    : {t.categ_id.complete_name}")
    print(f"  tracking : {t.tracking}")
    print(f"  uom      : {t.uom_id.name}")
    print(f"  exp_date : {t.use_expiration_date}")
    print(f"  seq      : {seq.prefix if seq and seq.prefix else 'sin secuencia'}")
    print()
