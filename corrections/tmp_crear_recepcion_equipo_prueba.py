wh = env['stock.warehouse'].search([('code', '=', 'AMP')], limit=1)
picking_type = env['stock.picking.type'].search([
    ('warehouse_id', '=', wh.id),
    ('code', '=', 'incoming'),
], limit=1)
producto = env['product.product'].search([('default_code', '=', 'EQAMC01')], limit=1)
proveedor = env['res.partner'].search([('supplier_rank', '>', 0)], limit=1)

picking = env['stock.picking'].sudo().create({
    'picking_type_id': picking_type.id,
    'partner_id': proveedor.id,
    'location_id': env.ref('stock.stock_location_suppliers').id,
    'location_dest_id': wh.wh_input_stock_loc_id.id,
})
env['stock.move'].sudo().create({
    'picking_id': picking.id,
    'product_id': producto.id,
    'product_uom_qty': 1.0,
    'product_uom': producto.uom_id.id,
    'location_id': env.ref('stock.stock_location_suppliers').id,
    'location_dest_id': wh.wh_input_stock_loc_id.id,
    'description_picking': producto.display_name,
})
picking.sudo().action_confirm()
env.cr.commit()
print(f"Recepción: {picking.name} (id={picking.id})")
print(f"URL: https://stagingfc.amunet.com.mx/odoo/inventory/receipts/{picking.id}")
