# Etapa B: PFIs Fapon ultimos 90 dias como purchase.order confirmadas + receipts EN ASSIGNED (almacen valida)
import json
from datetime import datetime
data = json.load(open('/tmp/po_historico_90d.json'))
data = [d for d in data if d['supplier']=='fapon']
print(f"PFIs Fapon a procesar: {len(data)}")

fapon = env['res.partner'].search([('name','ilike','Fapon')], limit=1)
mg_uom = env['uom.uom'].search([('name','=','mg')], limit=1)
usd = env.ref('base.USD')

def resolve_product(catalog_no):
    si = env['product.supplierinfo'].search([
        ('partner_id','=',fapon.id),('product_code','=',catalog_no)], limit=1)
    return (si.product_tmpl_id.product_variant_id, si.product_uom_id or mg_uom, si.price) if si else (None,None,0)

resultados=[]
for pfi in data:
    pfi_date = datetime.strptime(pfi['date'],'%Y-%m-%d').date()
    origin = pfi['pfi']
    existing = env['purchase.order'].search([('partner_id','=',fapon.id),('origin','=',origin)], limit=1)
    if existing:
        resultados.append({'pfi':origin,'po':existing.name,'state':existing.state,'skip':True})
        continue
    order_lines=[]
    for item in pfi['items']:
        prod,uom,default_price = resolve_product(item['catalog_no'])
        if not prod: continue
        order_lines.append((0,0,{
            'product_id':prod.id,
            'name':item['description'][:200] if item['description'] else item['catalog_no'],
            'product_qty':item['qty'],'product_uom_id':mg_uom.id,
            'price_unit':item['unit_price'] or default_price,'date_planned':pfi_date,
        }))
    if not order_lines: continue
    po = env['purchase.order'].create({
        'partner_id':fapon.id,'date_order':pfi_date,'date_planned':pfi_date,
        'origin':origin,'currency_id':usd.id,'order_line':order_lines,
    })
    po.button_confirm()
    # NO validar el picking - dejar en assigned para que almacen lo valide via UI
    env.cr.commit()
    pickings = po.picking_ids
    receipt_state = pickings[0].state if pickings else '-'
    resultados.append({'pfi':origin,'po':po.name,'state':po.state,'receipt':receipt_state,
                       'total':po.amount_total,'lines':len(order_lines)})

print("\n=== Resumen (receipts quedan PENDIENTES para almacen) ===")
for r in resultados:
    print(f"  {r['pfi']:30} PO={r.get('po')} state={r.get('state')} receipt={r.get('receipt','-')} total=${r.get('total',0)}")
