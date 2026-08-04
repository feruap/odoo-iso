tmpl = env['product.template'].with_context(active_test=False).search([
    ('default_code','=','STESP01')], limit=1)
prod = tmpl.product_variant_ids[:1]
lotes = env['stock.lot'].search([('product_id','=',prod.id)], order='name')
print(f"STESP01 — {tmpl.name}\n")
for l in lotes:
    quants = env['stock.quant'].search([('lot_id','=',l.id)])
    for q in quants:
        print(f"  Lote: {l.name} | Ubic: {q.location_id.complete_name} | Cant: {q.quantity} | Reservada: {q.reserved_quantity}")
