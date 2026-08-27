"""
SCRIPT DE PRODUCCION — ejecutar solo con autorización de Mery / Fernando.
Crea MPREC93 (Yodo), MPREC96 (Yoduro de Potasio), MPREC97 (Verde brillante)
y su recepción ya validada AMP/IN/... con los lotes y fechas capturados en staging.

Datos verificados en staging 2026-08-27 por Karla Fernanda Palma (almacenmp).
"""
import logging
from datetime import date
_logger = logging.getLogger(__name__)

# ── Datos de los reactivos ──────────────────────────────────────────────────
REACTIVOS = [
    {
        'code':    'MPREC93',
        'name':    'Yodo',
        'prefix':  'REC93',
        'qty':     100.0,
        'lote_interno':   'REC93082601',
        'lote_proveedor': 'ACP09571',
        'fecha_fab': '2025-03-03',
        'fecha_cad': '2028-03-03',
    },
    {
        'code':    'MPREC96',
        'name':    'Yoduro de Potasio',
        'prefix':  'REC96',
        'qty':     50.0,
        'lote_interno':   'REC96082601',
        'lote_proveedor': 'NA',
        'fecha_fab': None,
        'fecha_cad': '2031-08-01',
    },
    {
        'code':    'MPREC97',
        'name':    'Verde brillante',
        'prefix':  'REC97',
        'qty':     10.0,
        'lote_interno':   'REC97082601',
        'lote_proveedor': '2323-V2382',
        'fecha_fab': '2023-01-01',
        'fecha_cad': '2028-01-01',
    },
]

# ── Buscar referencias fijas ────────────────────────────────────────────────
categ = env['product.category'].search([('complete_name', '=', 'Materia prima / Reactivo')], limit=1)
if not categ:
    raise ValueError("No se encontró categoría 'Materia prima / Reactivo' — verifique antes de continuar")

uom = env['uom.uom'].search([('name', '=', 'Gramos')], limit=1)
if not uom:
    uom = env['uom.uom'].search([('name', 'ilike', 'gram')], limit=1)
if not uom:
    raise ValueError("No se encontró UoM Gramos")

# Mercado Libre
ml = env['res.partner'].search([('name', '=', 'Mercado Libre'), ('supplier_rank', '>', 0)], limit=1)
if not ml:
    ml = env['res.partner'].search([('name', 'ilike', 'Mercado Libre')], limit=1)
if not ml:
    ml = env['res.partner'].create({'name': 'Mercado Libre', 'is_company': True, 'supplier_rank': 1})
    _logger.info("Creado proveedor Mercado Libre id=%d", ml.id)
else:
    if ml.supplier_rank == 0:
        ml.write({'supplier_rank': 1})
    _logger.info("Proveedor Mercado Libre ya existe id=%d", ml.id)

# Tipo de operación: Recepciones
picking_type = env['stock.picking.type'].search([('code', '=', 'incoming')], order='id asc', limit=1)
src_loc = picking_type.default_location_src_id or env['stock.location'].search([('usage', '=', 'supplier')], limit=1)
dest_loc = picking_type.default_location_dest_id

# ── Crear productos ─────────────────────────────────────────────────────────
productos = {}
for r in REACTIVOS:
    existing = env['product.template'].with_context(active_test=False).search(
        [('default_code', '=', r['code']), ('active', '=', True)], limit=1)
    if existing:
        _logger.info("Producto %s ya existe (id=%d), usando el existente", r['code'], existing.id)
        productos[r['code']] = existing
        continue

    seq = env['ir.sequence'].create({
        'name': f"Lote {r['code']}",
        'code': f"amunet.lot.{r['prefix']}.prod",
        'prefix': f"{r['prefix']}%(month)s%(y)s",
        'padding': 2,
        'number_increment': 1,
        'number_next_actual': 1,
        'implementation': 'standard',
    })

    pt = env['product.template'].create({
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
    })
    env['product.supplierinfo'].create({
        'product_tmpl_id': pt.id,
        'partner_id': ml.id,
        'min_qty': 0,
        'price': 0,
    })
    _logger.info("Creado %s '%s' id=%d", r['code'], r['name'], pt.id)
    productos[r['code']] = pt

# ── Crear recepción validada ────────────────────────────────────────────────
picking = env['stock.picking'].create({
    'partner_id': ml.id,
    'picking_type_id': picking_type.id,
    'location_id': src_loc.id,
    'location_dest_id': dest_loc.id,
    'origin': 'Yodo / Yoduro de Potasio / Verde brillante - Mercado Libre',
})
_logger.info("Creado picking %s id=%d", picking.name, picking.id)

for r in REACTIVOS:
    pt = productos[r['code']]
    product = pt.product_variant_ids[:1]
    move = env['stock.move'].create({
        'product_id': product.id,
        'product_uom_qty': r['qty'],
        'product_uom': uom.id,
        'picking_id': picking.id,
        'location_id': src_loc.id,
        'location_dest_id': dest_loc.id,
        'amunet_supplier_lot': r['lote_proveedor'] or '',
        'amunet_mfg_date': r['fecha_fab'] or '',
        'amunet_exp_date': r['fecha_cad'] or '',
    })

# Confirmar picking
picking.action_confirm()
picking.action_assign()

# Crear lotes y llenar move lines
for r in REACTIVOS:
    pt = productos[r['code']]
    product = pt.product_variant_ids[:1]

    lote = env['stock.lot'].search([
        ('name', '=', r['lote_interno']),
        ('product_id', '=', product.id),
    ], limit=1)
    if not lote:
        lote_vals = {
            'name': r['lote_interno'],
            'product_id': product.id,
        }
        if r['fecha_fab']:
            lote_vals['use_date'] = r['fecha_fab']
        if r['fecha_cad']:
            lote_vals['expiration_date'] = r['fecha_cad']
        lote = env['stock.lot'].create(lote_vals)

    move = picking.move_ids.filtered(lambda m: m.product_id.id == product.id)[:1]
    sml = picking.move_line_ids.filtered(lambda l: l.product_id.id == product.id)
    if sml:
        sml.write({'lot_id': lote.id, 'quantity': r['qty']})
    else:
        env['stock.move.line'].create({
            'picking_id': picking.id,
            'move_id': move.id,
            'product_id': product.id,
            'lot_id': lote.id,
            'quantity': r['qty'],
            'location_id': src_loc.id,
            'location_dest_id': dest_loc.id,
        })

# Validar
picking.with_context(skip_backorder=True).button_validate()

env.cr.commit()
print(f"\nListo.")
print(f"  Recepción: {picking.name} (estado={picking.state})")
for r in REACTIVOS:
    pt = productos[r['code']]
    print(f"  {r['code']} {r['name']}: lote {r['lote_interno']}, {r['qty']} g")
