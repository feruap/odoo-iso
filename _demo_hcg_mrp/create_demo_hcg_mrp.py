# -*- coding: utf-8 -*-
from datetime import date, datetime

DEMO_TAG = 'DEMO-MRP-HCG-2000-20260510'
TODAY = date(2026, 5, 10)
EXPIRY = date(2028, 5, 10)
QTY_FINAL = 2000

PLAN = [
    ('SPHMT06',  'DEMO-SPHMT06-HCG-20260510',   70),
    ('MPMNC01',  'DEMO-MPMNC01-HCG-20260510',   70),
    ('SPALMA08', 'DEMO-SPALMA08-HCG-20260510', 2100),
    ('SPALMA01', 'DEMO-SPALMA01-HCG-20260510', 2100),
    ('MPAAB01',  'DEMO-MPAAB01-HCG-20260510',  2100),
    ('MPAFV01',  'DEMO-MPAFV01-HCG-20260510',  2100),
    ('MPCAR65',  'DEMO-MPCAR65-HCG-20260510',  2000),
    ('MPBOL01',  'DEMO-MPBOL01-HCG-20260510',  2000),
    ('STDSC01',  'DEMO-STDSC01-HCG-20260510',  2000),
    ('MICAJ10',  'DEMO-MICAJ10-HCG-20260510',   200),
]

FINAL_CODE = 'DMHCG03'
FINAL_LOT_NAME = DEMO_TAG

ANALYST_LOGIN = 'analista1cc@amunet.com.mx'
SUPERVISOR_LOGIN = 's.controldecalidad@amunet.com.mx'
SANITARY_LOGIN = 'desarrollo@amunet.com.mx'
WAREHOUSE_LOGIN = 'supalmacen@amunet.com.mx'


def log(msg):
    print('[DEMO-HCG-MRP]', msg)


def by_code(code):
    p = env['product.product'].search([('default_code', '=', code)], limit=1)
    if not p:
        raise Exception('Producto %s no encontrado' % code)
    return p


def by_lot(product, lot_name):
    l = env['stock.lot'].search([
        ('name', '=', lot_name),
        ('product_id', '=', product.id),
    ], limit=1)
    if not l:
        raise Exception('Lote %s para %s no encontrado' % (lot_name, product.default_code))
    return l


def by_user(login):
    u = env['res.users'].search([('login', '=', login), ('active', '=', True)], limit=1)
    if not u:
        raise Exception('Usuario %s no encontrado' % login)
    return u


def ensure_lot(product, lot_name, vals=None):
    vals = vals or {}
    lot = env['stock.lot'].search([
        ('name', '=', lot_name),
        ('product_id', '=', product.id),
    ], limit=1)
    if lot:
        return lot
    data = {
        'name': lot_name,
        'product_id': product.id,
        'company_id': env.company.id,
    }
    data.update(vals)
    return env['stock.lot'].sudo().create(data)


def set_quant(product, location, lot, target_qty):
    Quant = env['stock.quant'].sudo()
    current = sum(Quant.search([
        ('product_id', '=', product.id),
        ('location_id', '=', location.id),
        ('lot_id', '=', lot.id),
    ]).mapped('quantity'))
    delta = target_qty - current
    if abs(delta) > 0.00001:
        Quant._update_available_quantity(product, location, delta, lot_id=lot)
        log('Stock ajustado: %s lote=%s ubic=%s -> %s' % (
            product.default_code, lot.name, location.complete_name, target_qty
        ))


# 1) Productos / lotes / usuarios
final_product = by_code(FINAL_CODE)
products = {code: by_code(code) for (code, _, _) in PLAN}
lots = {code: by_lot(products[code], lot_name) for (code, lot_name, _) in PLAN}
users = {
    'warehouse': by_user(WAREHOUSE_LOGIN),
    'analyst': by_user(ANALYST_LOGIN),
    'supervisor': by_user(SUPERVISOR_LOGIN),
    'sanitary': by_user(SANITARY_LOGIN),
}
source_location = env['stock.location'].browse(5)
final_location = env['stock.location'].browse(14)

for code, lot_name, qty in PLAN:
    set_quant(products[code], source_location, lots[code], qty)


# 2) BOM demo
Bom = env['mrp.bom']
existing_bom = Bom.search([
    ('product_tmpl_id', '=', final_product.product_tmpl_id.id),
    ('code', '=', DEMO_TAG),
], limit=1)

if existing_bom:
    bom = existing_bom
    log('BOM demo ya existia: id=%s' % bom.id)
else:
    bom = Bom.create({
        'product_tmpl_id': final_product.product_tmpl_id.id,
        'product_id': final_product.id,
        'product_qty': QTY_FINAL,
        'product_uom_id': final_product.uom_id.id,
        'type': 'normal',
        'code': DEMO_TAG,
        'company_id': env.company.id,
        'bom_line_ids': [
            (0, 0, {
                'product_id': products[code].id,
                'product_qty': qty,
                'product_uom_id': products[code].uom_id.id,
            })
            for (code, _, qty) in PLAN
        ],
    })
    log('BOM demo creada: id=%s code=%s qty=%s lineas=%s' % (
        bom.id, bom.code, bom.product_qty, len(bom.bom_line_ids)
    ))


# 3) Lote final
final_lot = ensure_lot(final_product, FINAL_LOT_NAME, {
    'manufacturing_date': TODAY,
    'expiration_date': EXPIRY,
    'analysis_number': 'DEMO-AN-MRP-HCG-20260510-001',
})
log('Lote final: id=%s name=%s' % (final_lot.id, final_lot.name))


# 4) Manufacturing Order
Mrp = env['mrp.production']
existing_mo = Mrp.search([
    ('origin', '=', DEMO_TAG),
    ('product_id', '=', final_product.id),
], limit=1)

if existing_mo:
    mo = existing_mo
    log('MO ya existia: %s id=%s state=%s' % (mo.name, mo.id, mo.state))
else:
    mo_vals = {
        'product_id': final_product.id,
        'product_qty': QTY_FINAL,
        'product_uom_id': final_product.uom_id.id,
        'bom_id': bom.id,
        'date_start': datetime.combine(TODAY, datetime.min.time()),
        'origin': DEMO_TAG,
        'company_id': env.company.id,
        'location_src_id': source_location.id,
        'location_dest_id': final_location.id,
        'lot_producing_ids': [(6, 0, [final_lot.id])],
    }
    mo = Mrp.sudo().create(mo_vals)
    log('MO creada borrador: %s id=%s' % (mo.name, mo.id))
    mo.action_confirm()
    log('MO confirmada: state=%s moves=%s' % (mo.state, len(mo.move_raw_ids)))

if final_lot not in mo.lot_producing_ids:
    mo.lot_producing_ids = [(6, 0, [final_lot.id])]


# 5) Asignar lotes DEMO en cada move_raw
for move in mo.move_raw_ids:
    code = move.product_id.default_code
    if code not in lots:
        continue
    target_lot = lots[code]
    plan_qty = next((q for (c, _, q) in PLAN if c == code), move.product_uom_qty)
    move.move_line_ids.unlink()
    env['stock.move.line'].create({
        'move_id': move.id,
        'product_id': move.product_id.id,
        'product_uom_id': move.product_uom.id,
        'location_id': source_location.id,
        'location_dest_id': move.location_dest_id.id,
        'lot_id': target_lot.id,
        'quantity': plan_qty,
        'company_id': env.company.id,
    })

# 6) move_finished con el lote final
for move in mo.move_finished_ids:
    if move.product_id.id == final_product.id:
        move.move_line_ids.unlink()
        env['stock.move.line'].create({
            'move_id': move.id,
            'product_id': move.product_id.id,
            'product_uom_id': move.product_uom.id,
            'location_id': move.location_id.id,
            'location_dest_id': final_location.id,
            'lot_id': final_lot.id,
            'quantity': QTY_FINAL,
            'company_id': env.company.id,
        })

mo.qty_producing = QTY_FINAL

# 7) amunet_production checklist override
checklist_vals = {}
for fname in [
    'amunet_check_history_log',
    'amunet_check_calculations',
    'amunet_check_dilution',
    'amunet_check_aforar',
]:
    if fname in mo._fields:
        checklist_vals[fname] = True
if 'quality_analysis_status' in mo._fields:
    checklist_vals['quality_analysis_status'] = 'approved'
if checklist_vals:
    mo.write(checklist_vals)
    log('Checklist operativa marcada: %s' % checklist_vals)

# 8) Done
if mo.state != 'done':
    res = mo.button_mark_done()
    log('button_mark_done -> %r state=%s' % (res, mo.state))

if mo.state not in ('done',):
    log('MO state=%s, intentando con skip_consumption' % mo.state)
    ctx = {'skip_consumption': True, 'skip_immediate': True, 'skip_backorder': True}
    res2 = mo.with_context(**ctx).button_mark_done()
    log('button_mark_done(skip_consumption) -> %r state=%s' % (res2, mo.state))

log('MO final: %s id=%s state=%s qty_produced=%s' % (
    mo.name, mo.id, mo.state, mo.qty_produced
))

env.cr.commit()

print('DEMO_MRP_BOM_ID=%s' % bom.id)
print('DEMO_MRP_BOM_NAME=%s' % (bom.code or bom.display_name))
print('DEMO_MRP_MO_ID=%s' % mo.id)
print('DEMO_MRP_MO_NAME=%s' % mo.name)
print('DEMO_MRP_MO_STATE=%s' % mo.state)
print('DEMO_MRP_FINAL_LOT_ID=%s' % final_lot.id)
print('DEMO_MRP_FINAL_LOT_NAME=%s' % final_lot.name)
