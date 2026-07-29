"""
Crea una nueva recepción para SPHMC77 (Hoja Maestra Transglutaminasa IgA)
pendiente en PO P00170. Cantidad: 120 cm.

Karla quitó SPHMC77 de AMP/IN/00159 porque no llegó con el resto del pedido.
Se genera esta recepción de respaldo por si llega después.

Autorizado por: Karla Fernanda Palma Ramos (almacen.mp@amunet.com.mx)
Fecha: 2026-07-29
"""
po = env['purchase.order'].search([('name', '=', 'P00170')], limit=1)
tmpl = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'SPHMC77')], limit=1)
prod = tmpl.product_variant_ids[:1]

# Ubicaciones
loc_src  = env['stock.location'].search([('usage', '=', 'supplier')], limit=1)
loc_dest = env['stock.location'].search([('complete_name', 'ilike', 'AMP/Entrada')], limit=1)
picking_type = env['stock.picking.type'].search([
    ('code', '=', 'incoming'),
    ('warehouse_id.lot_stock_id.complete_name', 'ilike', 'AMP'),
], limit=1)

print(f"PO          : {po.name}")
print(f"Producto    : {prod.display_name}")
print(f"Tipo picking: {picking_type.name}")
print(f"Origen      : {loc_src.complete_name}")
print(f"Destino     : {loc_dest.complete_name}")
print()

picking = env['stock.picking'].sudo().create({
    'partner_id': po.partner_id.id,
    'picking_type_id': picking_type.id,
    'location_id': loc_src.id,
    'location_dest_id': loc_dest.id,
    'origin': po.name,
    'purchase_id': po.id,
})

move = env['stock.move'].sudo().create({
    'description_picking': tmpl.name,
    'product_id': prod.id,
    'product_uom_qty': 120.0,
    'product_uom': tmpl.uom_id.id,
    'picking_id': picking.id,
    'location_id': loc_src.id,
    'location_dest_id': loc_dest.id,
    'purchase_line_id': po.order_line.filtered(
        lambda l: l.product_id.id == prod.id)[:1].id,
})

picking.action_confirm()
picking.action_assign()

env.cr.commit()
print(f"✅ Recepción creada: {picking.name}")
print(f"   Producto : SPHMC77 — {tmpl.name}")
print(f"   Cantidad : 120 cm")
print(f"   Estado   : {picking.state}")
print(f"   PO origen: {po.name}")
