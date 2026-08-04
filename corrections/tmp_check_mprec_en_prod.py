"""
Solo lectura: verifica qué productos y lotes de MPREC existen en producción.
"""
codigos_nuevos = [
    'MPREC46','MPREC48','MPREC50','MPREC51','MPREC52','MPREC53','MPREC55',
    'MPREC56','MPREC65','MPREC66','MPREC67','MPREC70','MPREC73',
    'MPREC74','MPREC79','MPREC80','MPREC82','MPREC89',
]
codigos_batch1 = [
    'MPREC04','MPREC12','MPREC19','MPREC46','MPREC48','MPREC50',
    'MPREC51','MPREC52','MPREC53','MPREC55','MPREC61',
]
print("=== Productos nuevos ===")
for cod in codigos_nuevos:
    t = env['product.template'].with_context(active_test=False).search([('default_code','=',cod)], limit=1)
    print(f"  {cod}: {'✅ existe' if t else '❌ falta'} {('— '+t.name) if t else ''}")

print()
print("=== Lotes (batch 1 — debería estar) ===")
for cod in codigos_batch1:
    t = env['product.template'].with_context(active_test=False).search([('default_code','=',cod)], limit=1)
    if not t:
        print(f"  {cod}: producto no existe")
        continue
    prod = t.product_variant_ids[:1]
    lotes = env['stock.lot'].search([('product_id','=',prod.id)])
    if lotes:
        for l in lotes:
            print(f"  {cod}: lote {l.name} | prov={l.factory_lot_id.name if l.factory_lot_id else '-'}")
    else:
        print(f"  {cod}: ⚠️  sin lotes")

print()
print("=== MPREC17 ===")
t17 = env['product.template'].with_context(active_test=False).search([('default_code','=','MPREC17')], limit=1)
prod17 = t17.product_variant_ids[:1]
lotes17 = env['stock.lot'].search([('product_id','=',prod17.id)])
if lotes17:
    for l in lotes17:
        print(f"  lote {l.name} | prov={l.factory_lot_id.name if l.factory_lot_id else '-'}")
else:
    print("  sin lotes")
