"""
Crea la recepción AMP/IN/... para MPREC93, MPREC96, MPREC97
Proveedor: Mercado Libre
Cantidades: 100 g / 50 g / 10 g respectivamente
Karla llenará lote, fechas de fabricación y caducidad antes de validar.
"""
import logging
_logger = logging.getLogger(__name__)

LINEAS = [
    {'code': 'MPREC93', 'qty': 100.0},
    {'code': 'MPREC96', 'qty': 50.0},
    {'code': 'MPREC97', 'qty': 10.0},
]

# Proveedor
ml = env['res.partner'].search([('name', '=', 'Mercado Libre'), ('supplier_rank', '>', 0)], limit=1)
if not ml:
    raise ValueError("No se encontró proveedor Mercado Libre")

# Tipo de operación: recepción (incoming) del almacén principal
picking_type = env['stock.picking.type'].search([
    ('code', '=', 'incoming'),
    ('warehouse_id.name', '!=', False),
], limit=1)
if not picking_type:
    raise ValueError("No se encontró tipo de operación de entrada")

# Ubicaciones
src_loc = picking_type.default_location_src_id or env['stock.location'].search([('usage', '=', 'supplier')], limit=1)
dest_loc = picking_type.default_location_dest_id

# Crear picking
picking = env['stock.picking'].create({
    'partner_id': ml.id,
    'picking_type_id': picking_type.id,
    'location_id': src_loc.id,
    'location_dest_id': dest_loc.id,
    'origin': 'Yodo / Yoduro de Potasio / Verde brillante - Mercado Libre',
})

for l in LINEAS:
    pt = env['product.template'].search([('default_code', '=', l['code']), ('active', '=', True)], limit=1)
    if not pt:
        _logger.warning("No se encontró producto %s", l['code'])
        continue
    product = pt.product_variant_ids[:1]
    env['stock.move'].create({
        'product_id': product.id,
        'product_uom_qty': l['qty'],
        'product_uom': pt.uom_id.id,
        'picking_id': picking.id,
        'location_id': src_loc.id,
        'location_dest_id': dest_loc.id,
    })

env.cr.commit()
print(f"Recepción creada: {picking.name} (id={picking.id})")
print(f"Tipo: {picking_type.name} | Destino: {dest_loc.complete_name}")
