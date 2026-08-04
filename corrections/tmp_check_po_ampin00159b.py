"""Revisa PO P00170 y estado de SPHMC77."""
po = env['purchase.order'].search([('name', '=', 'P00170')], limit=1)
print(f"PO: {po.name} | estado={po.state}\n")

for line in po.order_line:
    if 'SPHMC77' in (line.product_id.default_code or ''):
        uom_name = line.product_uom_id.name if hasattr(line, 'product_uom_id') else '?'
        print(f"  [{line.product_id.default_code}] {line.product_id.name}")
        print(f"    qty pedida   : {line.product_qty} {uom_name}")
        print(f"    qty recibida : {line.qty_received}")
        print(f"    pendiente    : {line.product_qty - line.qty_received}")

# Movimientos pendientes de SPHMC77
tmpl = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'SPHMC77')], limit=1)
prod = tmpl.product_variant_ids[:1]
pendientes = env['stock.move'].search([
    ('product_id', '=', prod.id),
    ('state', 'not in', ['done', 'cancel']),
])
print(f"\nMovimientos pendientes de SPHMC77: {len(pendientes)}")
for m in pendientes:
    print(f"  {m.picking_id.name or '-'} | estado={m.state} | qty={m.product_uom_qty}")
