# Nuevo ingreso: Hoja Maestra Dimero D (SPHMC39), 58 cm.
# Lote Amunet HMC39072601 | Lote proveedor C00926060001 | Caducidad 2028-05-01
# Proveedor: Hangzhou Tongzhou Biotechnology (id 321). Requiere cuarentena/QC.
# Autorizado por Fernando 2026-07-20.
from odoo import fields
prod = env['product.product'].search([('default_code', '=', 'SPHMC39')], limit=1)
assert prod, 'no existe SPHMC39'
pt = env['stock.picking.type'].browse(1)  # Recepciones AMP
src = pt.default_location_src_id or env.ref('stock.stock_location_suppliers')
dest = pt.default_location_dest_id       # AMP/Entrada (se redirige a Control de calidad)

picking = env['stock.picking'].create({
    'picking_type_id': pt.id,
    'partner_id': 321,
    'location_id': src.id,
    'location_dest_id': dest.id,
    'origin': 'Ingreso manual SPHMC39 - autorizado Fernando 2026-07-20',
})
move = env['stock.move'].create({
    'description_picking': prod.display_name,
    'picking_id': picking.id,
    'product_id': prod.id,
    'product_uom_qty': 58.0,
    'product_uom': prod.uom_id.id,
    'location_id': src.id,
    'location_dest_id': dest.id,
})
picking.action_confirm()
# crea/asegura la move line con lote, cantidad y caducidad
ml = move.move_line_ids[:1]
if not ml:
    ml = env['stock.move.line'].create({
        'move_id': move.id, 'picking_id': picking.id, 'product_id': prod.id,
        'product_uom_id': prod.uom_id.id, 'location_id': src.id, 'location_dest_id': dest.id,
    })
ml.write({'lot_name': 'HMC39072601', 'quantity': 58.0,
          'expiration_date': '2028-05-01 09:00:00'})
# el lote de proveedor va en el move -> genera factory_lot y lo propaga a la linea
move.write({'amunet_supplier_lot': 'C00926060001'})
print('Picking:', picking.name, '| move_line factory_lot:', ml.factory_lot_id.name)
# validar (sin wizard de PIN); crea QC y enruta a cuarentena
picking.with_context(_skip_pin_wizard=True).button_validate()
print('Estado picking:', picking.state)
lot = env['stock.lot'].search([('name', '=', 'HMC39072601'), ('product_id', '=', prod.id)], limit=1)
print('Lote:', lot.name, '| caducidad:', lot.expiration_date, '| factory_lot:', lot.factory_lot_id.name)
qc = env['amunet.quality.check'].search([('lot_id', '=', lot.id)])
print('QC generado(s):', qc.mapped('analysis_number'), '| estado:', qc.mapped('state'))
quants = env['stock.quant'].search([('lot_id', '=', lot.id), ('quantity', '>', 0)])
for q in quants:
    print('  Ubicacion:', q.location_id.complete_name, '=', q.quantity)
env.cr.commit()
