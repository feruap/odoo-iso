# Alta en prod de MPREC90/MPREC91 (reactivos) con lote proveedor, lote Amunet,
# caducidad y existencia. Datos de Almacen (Karla) via mensaje 2026-07-17.
# Autorizado por Fernando 2026-07-21.
categ = env['product.category'].browse(18)  # Materia prima / Reactivo
ref = env['product.product'].search([('default_code', '=', 'MPREC01')], limit=1)  # gramos
gramos = ref.uom_id
STOCK = env.ref('stock.stock_location_stock')  # AMP/Existencias
items = [
    ('MPREC90', 'Agar bacteriológico', 'AB-2512140', 'REC90072601', '2029-12-30', 450.0),
    ('MPREC91', 'Base Agar Sangre',    '724123H005', 'REC91072601', '2028-08-01', 100.0),
]
for code, name, sup_lot, amunet_lot, cad, qty in items:
    if env['product.template'].search([('default_code', '=', code)], limit=1):
        print('OMITIDO %s: ya existe' % code); continue
    tmpl = env['product.template'].with_context(amunet_alta_autorizada=True).create({
        'name': name, 'default_code': code, 'categ_id': categ.id,
        'type': ref.type, 'is_storable': True, 'tracking': 'lot',
        'use_expiration_date': True, 'uom_id': gramos.id})
    prod = tmpl.product_variant_id
    fl = env['amunet.lot.factory'].sudo().search([('name', '=', sup_lot)], limit=1)
    if not fl:
        fl = env['amunet.lot.factory'].sudo().create({'name': sup_lot})
    lot = env['stock.lot'].sudo().create({
        'name': amunet_lot, 'product_id': prod.id, 'company_id': env.company.id,
        'expiration_date': cad + ' 09:00:00', 'factory_lot_id': fl.id})
    q = env['stock.quant'].with_context(inventory_mode=True).create({
        'product_id': prod.id, 'location_id': STOCK.id, 'lot_id': lot.id,
        'inventory_quantity': qty})
    q.action_apply_inventory()
    print('%s "%s" | lote %s (prov %s) | cad %s | %s g en %s' % (
        code, name, amunet_lot, sup_lot, cad, qty, STOCK.complete_name))
env.cr.commit()
print('MIGRACION MPREC90/91 OK')
