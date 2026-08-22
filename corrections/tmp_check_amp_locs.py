wh = env['stock.warehouse'].search([('code', '=', 'AMP')], limit=1)
print(f"Almacén: {wh.name}")
print(f"lot_stock_id: {wh.lot_stock_id.complete_name} (id={wh.lot_stock_id.id})")
print(f"wh_input: {wh.wh_input_stock_loc_id.complete_name} (id={wh.wh_input_stock_loc_id.id})")

parent = wh.lot_stock_id.location_id
print(f"Parent de lot_stock: {parent.complete_name} (id={parent.id})")

qc = env['stock.location'].search([
    ('location_id', '=', parent.id),
    ('usage', '=', 'internal'),
    ('name', 'ilike', 'calidad'),
], limit=1)
print(f"QC loc: {qc.complete_name if qc else 'NO ENCONTRADA'} (id={qc.id if qc else None})")

# Última recepción en cualquier estado
picking = env['stock.picking'].search([
    ('picking_type_code', '=', 'incoming'),
    ('picking_type_id.warehouse_id.code', '=', 'AMP'),
], order='id desc', limit=1)
if picking:
    print(f"\nÚltima recepción: {picking.name} estado={picking.state}")
    print(f"  dest header: {picking.location_dest_id.complete_name}")
    for m in picking.move_ids:
        req_q = m.product_id.product_tmpl_id._amunet_effective_requires_quarantine()
        print(f"  [{m.product_id.default_code}] requires_q={req_q} dest={m.location_dest_id.complete_name}")
