# 11 ingresos de hojas maestras. Proveedor Hangzhou Tongzhou (id 321).
# Caducidad 2028-05-01, fabricacion junio 2026. Lote interno patron HMC##072601.
# Autorizado por Fernando 2026-07-20.
items = [
    ('SPHMC33', 60,  'T00326060002'),   # CA 125
    ('SPHMC27', 150, 'I00826060001'),   # Rotavirus/Adenovirus
    ('SPHMC59', 60,  'C00826060001'),   # NT-proBNP
    ('SPHMC28', 150, 'I06026060001'),   # Tuberculosis
    ('SPHMC55', 30,  'O0082606000-1'),  # Calprotectina
    ('SPHMC48', 30,  'I01226060003'),   # Entamoeba
    ('SPHMC05', 60,  'I02526060002'),   # Chagas
    ('SPHMC06', 180, 'I09926060003'),   # VIH 1.2
    ('SPHMC32', 30,  'I04826060001'),   # Mycoplasma
    ('SPHMC42', 90,  'O01226060001'),   # Factor reumatoide
    ('SPHMC43', 60,  'I03526060002'),   # Tifoidea
]
pt = env['stock.picking.type'].browse(1)
src = pt.default_location_src_id or env.ref('stock.stock_location_suppliers')
dest = pt.default_location_dest_id
PARTNER = 321

for code, qty, lote_prov in items:
    prod = env['product.product'].search([('default_code', '=', code)], limit=1)
    if not prod:
        print('OMITIDO %s: producto no existe' % code); continue
    base = 'HMC' + code[5:] + '0726'
    n = 1
    while env['stock.lot'].search_count([('name', '=', base + '%02d' % n), ('product_id', '=', prod.id)]):
        n += 1
    lot_name = base + '%02d' % n
    picking = env['stock.picking'].create({
        'picking_type_id': pt.id, 'partner_id': PARTNER,
        'location_id': src.id, 'location_dest_id': dest.id,
        'origin': 'Ingreso HM lote julio2026 - autorizado Fernando 2026-07-20',
    })
    move = env['stock.move'].create({
        'description_picking': prod.display_name, 'picking_id': picking.id,
        'product_id': prod.id, 'product_uom_qty': float(qty), 'product_uom': prod.uom_id.id,
        'location_id': src.id, 'location_dest_id': dest.id,
    })
    picking.action_confirm()
    ml = move.move_line_ids[:1]
    if not ml:
        ml = env['stock.move.line'].create({
            'move_id': move.id, 'picking_id': picking.id, 'product_id': prod.id,
            'product_uom_id': prod.uom_id.id, 'location_id': src.id, 'location_dest_id': dest.id})
    ml.write({'lot_name': lot_name, 'quantity': float(qty), 'expiration_date': '2028-05-01 09:00:00'})
    move.write({'amunet_supplier_lot': lote_prov, 'amunet_mfg_date': '01/06/2026'})
    picking.with_context(_skip_pin_wizard=True).button_validate()
    lot = env['stock.lot'].search([('name', '=', lot_name), ('product_id', '=', prod.id)], limit=1)
    qc = env['amunet.quality.check'].search([('lot_id', '=', lot.id)])
    q = env['stock.quant'].search([('lot_id', '=', lot.id), ('quantity', '>', 0)])
    print('%s | %s | %s=%scm | lote %s | prov %s | cad %s | QC:%s | %s' % (
        picking.name, code, prod.default_code, qty, lot_name, lot.factory_lot_id.name,
        (lot.expiration_date.date() if lot.expiration_date else '?'),
        len(qc), ','.join('%s=%s' % (x.location_id.name, x.quantity) for x in q)))
    env.cr.commit()
print('LISTO')
