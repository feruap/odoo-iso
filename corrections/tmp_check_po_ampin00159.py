"""Busca la orden de compra origen de AMP/IN/00159 y el estado de SPHMC77."""
picking = env['stock.picking'].search([('name', '=', 'AMP/IN/00159')], limit=1)
po_name = picking.origin or '-'
print(f"Origen de AMP/IN/00159: {po_name}\n")

# Buscar la PO
po = env['purchase.order'].search([('name', '=', po_name)], limit=1)
if not po:
    # Intentar por purchase_id en el picking
    po = picking.purchase_id
if po:
    print(f"Orden de compra: {po.name} | estado={po.state}")
    for line in po.order_line:
        if 'SPHMC77' in (line.product_id.default_code or ''):
            print(f"\n  SPHMC77 en PO:")
            print(f"    qty pedida  : {line.product_qty} {line.product_uom.name}")
            print(f"    qty recibida: {line.qty_received}")
            print(f"    qty pendiente: {line.product_qty - line.qty_received}")
else:
    print("No se encontró la PO ligada")
    print(f"purchase_id del picking: {picking.purchase_id.name if picking.purchase_id else 'ninguno'}")

# Ver si hay otra recepción pendiente para SPHMC77
tmpl = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'SPHMC77')], limit=1)
prod = tmpl.product_variant_ids[:1]
pendientes = env['stock.move'].search([
    ('product_id', '=', prod.id),
    ('state', 'not in', ['done', 'cancel']),
])
print(f"\nMovimientos pendientes de SPHMC77: {len(pendientes)}")
for m in pendientes:
    print(f"  {m.picking_id.name or '-'} | {m.state} | qty={m.product_uom_qty}")
