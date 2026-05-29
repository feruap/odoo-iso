# Etapa B: cargar PFIs Fapon ultimos 90 dias como purchase.order confirmadas + recepciones validadas
# Solo Fapon (los demas no llegaron). Idempotente.
import json
from datetime import datetime
from collections import defaultdict

data = json.load(open('/tmp/po_historico_90d.json'))
data = [d for d in data if d['supplier']=='fapon']
print(f"PFIs Fapon a procesar: {len(data)}")

fapon = env['res.partner'].search([('name','ilike','Fapon International')], limit=1)
if not fapon:
    print("ERROR: Fapon no existe - corre etapa A primero")
    exit()

mg_uom = env['uom.uom'].search([('name','=','mg')], limit=1)
usd = env.ref('base.USD')

def resolve_product(catalog_no):
    si = env['product.supplierinfo'].search([
        ('partner_id','=',fapon.id),
        ('product_code','=', catalog_no)
    ], limit=1)
    if si:
        return si.product_tmpl_id.product_variant_id, si.product_uom_id or mg_uom, si.price
    return None, None, 0

resultados = []
no_resueltos = []
for pfi in data:
    pfi_date = datetime.strptime(pfi['date'],'%Y-%m-%d').date()
    origin = pfi['pfi']
    # Idempotencia
    existing = env['purchase.order'].search([('partner_id','=',fapon.id),('origin','=',origin)], limit=1)
    if existing:
        # Si ya existe pero receipt aun no done, validar
        for pick in existing.picking_ids:
            if pick.state in ('assigned','partially_available','confirmed'):
                try:
                    for move in pick.move_ids:
                        if hasattr(move, 'quantity'): move.quantity = move.product_uom_qty
                        elif hasattr(move, 'quantity_done'): move.quantity_done = move.product_uom_qty
                    pick.with_context(skip_backorder=True, picking_ids_not_to_backorder=[pick.id]).button_validate()
                except: pass
        resultados.append({'pfi':origin,'po':existing.name,'state':existing.state,'skip':True})
        continue

    order_lines = []
    for item in pfi['items']:
        prod, uom, default_price = resolve_product(item['catalog_no'])
        if not prod:
            no_resueltos.append(f"{item['catalog_no']} | {item['description'][:60]}")
            continue
        order_lines.append((0,0,{
            'product_id': prod.id,
            'name': item['description'][:200] if item['description'] else f"{item['catalog_no']}",
            'product_qty': item['qty'],
            'product_uom_id': mg_uom.id,
            'price_unit': item['unit_price'] or default_price,
            'date_planned': pfi_date,
        }))
    if not order_lines:
        resultados.append({'pfi':origin,'po':None,'state':'no_lines','skip':False})
        continue

    po = env['purchase.order'].create({
        'partner_id': fapon.id,
        'date_order': pfi_date,
        'date_planned': pfi_date,
        'origin': origin,
        'currency_id': usd.id,
        'order_line': order_lines,
    })
    po.button_confirm()
    env.cr.commit()

    # Validar recepcion con API Odoo 19 (campo 'quantity')
    for pick in po.picking_ids:
        try:
            for move in pick.move_ids:
                if hasattr(move, 'quantity'): move.quantity = move.product_uom_qty
                elif hasattr(move, 'quantity_done'): move.quantity_done = move.product_uom_qty
            pick.with_context(skip_backorder=True, picking_ids_not_to_backorder=[pick.id]).button_validate()
        except Exception as e:
            print(f"  AVISO validar {pick.name}: {str(e)[:100]}")
    env.cr.commit()
    resultados.append({'pfi':origin,'po':po.name,'state':po.state,'total':po.amount_total,'lines':len(order_lines)})

print("\n=== Resumen ===")
for r in resultados:
    print(f"  {r['pfi']}: PO={r.get('po')} state={r.get('state')} lines={r.get('lines','-')} total=${r.get('total',0)}")
if no_resueltos:
    print(f"\n  No resueltos: {len(no_resueltos)}")
    for x in no_resueltos: print(f"     - {x}")
