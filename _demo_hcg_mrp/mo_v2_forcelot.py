# -*- coding: utf-8 -*-
"""MO V2: forzar lot_producing_ids despues del create para que amunet_production
no lo sobreescriba con un lote auto-generado."""
from datetime import date, datetime

DEMO_TAG = 'DEMO-MRP-HCG-2000-20260510-V2'
TODAY = date(2026, 5, 10)
QTY_FINAL = 2000
BOM_ID = 3
FINAL_CODE = 'DMHCG03'

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

def log(m): print('[V2-FORCE]', m)

final_product = env['product.product'].search([('default_code','=', FINAL_CODE)], limit=1)
products = {c: env['product.product'].search([('default_code','=', c)], limit=1) for (c,_,_) in PLAN}
lots = {c: env['stock.lot'].search([('name','=', ln)], limit=1) for (c,ln,_) in PLAN}
final_lot = env['stock.lot'].search([('name','=', DEMO_TAG)], limit=1)
log('Lote final V2 esperado: id=%s name=%s' % (final_lot.id, final_lot.name))
source_location = env['stock.location'].browse(5)
final_location = env['stock.location'].browse(14)

# Reset stock
Quant = env['stock.quant'].sudo()
for code, _, qty in PLAN:
    p = products[code]; l = lots[code]
    cur = sum(Quant.search([('product_id','=', p.id),('location_id','=', source_location.id),('lot_id','=', l.id)]).mapped('quantity'))
    if cur < qty:
        Quant._update_available_quantity(p, source_location, qty-cur, lot_id=l)
env.cr.commit()

# Crear MO sin lot_producing_ids inicial (para que el override no compita)
mo = env['mrp.production'].sudo().create({
    'product_id': final_product.id,
    'product_qty': QTY_FINAL,
    'product_uom_id': final_product.uom_id.id,
    'bom_id': BOM_ID,
    'date_start': datetime.combine(TODAY, datetime.min.time()),
    'origin': DEMO_TAG,
    'company_id': env.company.id,
    'location_src_id': source_location.id,
    'location_dest_id': final_location.id,
})
log('MO creada (sin lote): id=%s solution_lot=%s producing=%s' % (
    mo.id, mo.solution_lot_id, mo.lot_producing_ids.mapped('name')))

# Borrar lote auto-generado por amunet_production y forzar el V2
auto_lots = mo.lot_producing_ids
mo.lot_producing_ids = [(5, 0, 0)]  # vaciar
for al in auto_lots:
    if al.id != final_lot.id and al.product_id.id == final_product.id:
        # Liberar quants si los hay
        qts = env['stock.quant'].sudo().search([('lot_id','=', al.id)])
        for q in qts:
            env['stock.quant'].sudo()._update_available_quantity(al.product_id, q.location_id, -q.quantity, lot_id=al)
        try:
            al.sudo().unlink()
            log('Lote auto borrado: %s' % al.name)
        except Exception as e:
            log('Lote auto no borrado (se queda huerfano): %s -> %s' % (al.name, e))

mo.lot_producing_ids = [(6, 0, [final_lot.id])]
mo.solution_lot_id = final_lot.name
log('Lote forzado: producing=%s' % mo.lot_producing_ids.mapped('name'))

# Confirm
mo.action_confirm()
mo.action_assign()
log('confirm+assign state=%s wo=%s' % (mo.state, len(mo.workorder_ids)))

# Re-verificar lote despues de confirm
log('Post-confirm lot_producing_ids: %s' % mo.lot_producing_ids.mapped('name'))
if final_lot not in mo.lot_producing_ids:
    mo.lot_producing_ids = [(6, 0, [final_lot.id])]
    log('Re-forzado V2')

# Setear consumo en raws
for move in mo.move_raw_ids:
    code = move.product_id.default_code
    if code not in lots:
        continue
    lot = lots[code]
    plan_qty = next((q for (c, _, q) in PLAN if c == code), move.product_uom_qty)
    move.move_line_ids.unlink()
    env['stock.move.line'].create({
        'move_id': move.id,
        'product_id': move.product_id.id,
        'product_uom_id': move.product_uom.id,
        'location_id': source_location.id,
        'location_dest_id': move.location_dest_id.id,
        'lot_id': lot.id,
        'quantity': plan_qty,
        'company_id': env.company.id,
    })
    move.with_context(bypass_reservation_update=True).quantity = plan_qty
    move.picked = True

mo.qty_producing = QTY_FINAL

# Checklist
chk = {}
for fname in ['amunet_check_history_log','amunet_check_calculations',
              'amunet_check_dilution','amunet_check_aforar']:
    if fname in mo._fields:
        chk[fname] = True
if 'quality_analysis_status' in mo._fields:
    chk['quality_analysis_status'] = 'approved'
if chk:
    mo.write(chk)

# Workorders done
for wo in mo.workorder_ids:
    if wo.state not in ('done','cancel'):
        try:
            if wo.state == 'pending':
                wo.button_start()
            wo.button_finish()
        except Exception:
            pass

log('Pre-mark_done: state=%s, lot_producing_ids=%s' % (mo.state, mo.lot_producing_ids.mapped('name')))

res = mo.button_mark_done()
log('mark_done -> %s state=%s' % (type(res).__name__, mo.state))
if isinstance(res, dict) and res.get('res_model') == 'mrp.consumption.warning':
    wiz_ctx = res.get('context', {})
    Wiz = env['mrp.consumption.warning'].with_context(**wiz_ctx)
    wiz = Wiz.create({
        'mrp_production_ids': wiz_ctx.get('default_mrp_production_ids', [(6,0,[mo.id])]),
        'mrp_consumption_warning_line_ids': wiz_ctx.get('default_mrp_consumption_warning_line_ids', []),
    })
    res2 = wiz.action_confirm()
    log('wiz.confirm -> state=%s' % mo.state)

env.cr.commit()
log('--- FINAL ---')
log('lot_producing_ids: %s' % mo.lot_producing_ids.mapped('name'))
for m in mo.move_finished_ids:
    log('  fin %s qty=%s state=%s lot_ids=%s' % (
        m.product_id.default_code, m.quantity, m.state, m.lot_ids.mapped('name')))

print('MO_V2_ID=%s' % mo.id)
print('MO_V2_NAME=%s' % mo.name)
print('MO_V2_STATE=%s' % mo.state)
print('LOT_PRODUCING=%s' % ','.join(mo.lot_producing_ids.mapped('name')))
