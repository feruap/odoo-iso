"""Solo lectura: verifica si los nuevos MPREC ya están en producción."""
pendientes = ['MPREC74', 'MPREC79', 'MPREC80', 'MPREC82', 'MPREC89']
print("=== Productos pendientes ===")
for cod in pendientes:
    t = env['product.template'].with_context(active_test=False).search([('default_code','=',cod)], limit=1)
    print(f"  {cod}: {'✅ ya está — '+t.name if t else '❌ aún falta'}")

print()
print("=== Lotes batch 2+3 (muestra) ===")
checks = [
    ('MPREC56', 'REC56032501'),
    ('MPREC67', 'REC67032501'),
    ('MPREC82', 'REC82032501'),
]
for cod, lot_name in checks:
    t = env['product.template'].with_context(active_test=False).search([('default_code','=',cod)], limit=1)
    if not t:
        print(f"  {lot_name}: producto {cod} no existe")
        continue
    prod = t.product_variant_ids[:1]
    l = env['stock.lot'].search([('name','=',lot_name),('product_id','=',prod.id)], limit=1)
    print(f"  {lot_name}: {'✅ cargado' if l else '❌ falta'}")

print()
print("=== Lotes batch 4 (muestra) ===")
checks4 = [
    ('MPREC89', 'REC89032501'),
    ('MPREC17', 'REC17032501'),
    ('MPREC80', 'REC80032501'),
]
for cod, lot_name in checks4:
    t = env['product.template'].with_context(active_test=False).search([('default_code','=',cod)], limit=1)
    if not t:
        print(f"  {lot_name}: producto {cod} no existe")
        continue
    prod = t.product_variant_ids[:1]
    l = env['stock.lot'].search([('name','=',lot_name),('product_id','=',prod.id)], limit=1)
    print(f"  {lot_name}: {'✅ cargado' if l else '❌ falta'}")

print()
print("=== Secuencia STESP01 ===")
tmpl_esp = env['product.template'].with_context(active_test=False).search([('default_code','=','STESP01')],limit=1)
seq_esp = tmpl_esp.product_variant_ids[:1].lot_sequence_id
print(f"  STESP01 secuencia: {seq_esp.prefix if seq_esp and seq_esp.prefix else '❌ genérica / sin configurar'}")

print()
print("=== Ajuste ESP01072601 ===")
t_esp = env['product.template'].with_context(active_test=False).search([('default_code','=','STESP01')],limit=1)
prod_esp = t_esp.product_variant_ids[:1]
lot_esp = env['stock.lot'].search([('name','=','ESP01072601'),('product_id','=',prod_esp.id)],limit=1)
if lot_esp:
    q = env['stock.quant'].search([('lot_id','=',lot_esp.id),('location_id.usage','=','internal')],limit=1)
    qty = q.quantity if q else 0
    print(f"  ESP01072601 en AMP/Existencias: {qty} {'✅ ya en 0' if qty==0 else '❌ aún muestra '+str(qty)}")
