"""
Crea MPREC93 (Yodo), MPREC96 (Yoduro de Potasio) y MPREC97 (Verde brillante)
con la misma configuración que los MPREC existentes (tracking=lot, gramos,
categoría Materia prima / Reactivo, cuarentena, secuencia propia).
También crea Mercado Libre como proveedor si no existe.
"""
import logging
_logger = logging.getLogger(__name__)

REACTIVOS = [
    {'code': 'MPREC93', 'name': 'Yodo',                 'prefix': 'REC93'},
    {'code': 'MPREC96', 'name': 'Yoduro de Potasio',    'prefix': 'REC96'},
    {'code': 'MPREC97', 'name': 'Verde brillante',       'prefix': 'REC97'},
]

# Categoría
categ = env['product.category'].search([('complete_name', '=', 'Materia prima / Reactivo')], limit=1)
if not categ:
    raise ValueError("No se encontró la categoría 'Materia prima / Reactivo'")

# UoM Gramos
uom = env['uom.uom'].search([('name', 'ilike', 'gramo')], limit=1)
if not uom:
    raise ValueError("No se encontró la UoM 'Gramos'")

# Ubicaciones
prod_loc = env['stock.location'].search([('complete_name', 'ilike', 'Producción'), ('usage', '=', 'production')], limit=1)
inv_loc = env['stock.location'].search([('complete_name', 'ilike', 'Ajuste'), ('usage', '=', 'inventory')], limit=1)

# Mercado Libre como proveedor
ml = env['res.partner'].search([('name', 'ilike', 'Mercado Libre')], limit=1)
if not ml:
    ml = env['res.partner'].create({
        'name': 'Mercado Libre',
        'is_company': True,
        'supplier_rank': 1,
    })
    _logger.info("Creado proveedor Mercado Libre id=%d", ml.id)
else:
    _logger.info("Proveedor Mercado Libre ya existe id=%d", ml.id)

for r in REACTIVOS:
    # Verificar si ya existe
    existing = env['product.template'].search([('default_code', '=', r['code'])], limit=1)
    if existing:
        _logger.info("Ya existe %s (id=%d), omitiendo", r['code'], existing.id)
        continue

    # Crear secuencia de lote
    seq = env['ir.sequence'].create({
        'name': f"Lote {r['code']}",
        'code': f"amunet.lot.{r['code'].lower()}",
        'prefix': f"{r['prefix']}%(month)s%(y)s",
        'padding': 2,
        'number_increment': 1,
        'number_next_actual': 1,
        'implementation': 'standard',
    })

    vals = {
        'name': r['name'],
        'default_code': r['code'],
        'type': 'consu',
        'is_storable': True,
        'categ_id': categ.id,
        'uom_id': uom.id,
        'tracking': 'lot',
        'lot_sequence_id': seq.id,
        'amunet_lot_reset_monthly': True,
        'amunet_requires_quarantine': False,
        'amunet_req_quality_control': True,
        'amunet_req_history_log': True,
        'amunet_req_calculations': True,
        'amunet_req_dilution': True,
        'amunet_req_aforar': True,
        'sale_ok': True,
        'purchase_ok': True,
        'active': True,
        'purchase_method': 'receive',
        'expiration_time': 0,
        'use_time': 0,
        'removal_time': 0,
        'alert_time': 0,
    }
    if prod_loc:
        vals['property_stock_production'] = prod_loc.id
    if inv_loc:
        vals['property_stock_inventory'] = inv_loc.id

    pt = env['product.template'].create(vals)
    _logger.info("Creado %s '%s' id=%d seq_prefix=%s", r['code'], r['name'], pt.id, seq.prefix)

    # Agregar Mercado Libre como proveedor
    env['product.supplierinfo'].create({
        'product_tmpl_id': pt.id,
        'partner_id': ml.id,
        'min_qty': 0,
        'price': 0,
    })

env.cr.commit()
print("Listo. MPREC93, MPREC96 y MPREC97 creados con Mercado Libre como proveedor.")
