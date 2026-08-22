tmpl = env['product.template'].search([('default_code','=','MPREC32')], limit=1)
prod = tmpl.product_variant_ids[:1]
lotes = env['stock.lot'].search([('product_id','=',prod.id)], order='name')
print(f"{tmpl.default_code} — {tmpl.name} (UoM: {tmpl.uom_id.name})\n")
print(f"{'Lote Amunet':<16} {'Lote proveedor':<20} {'Caducidad':<14} {'Cantidad'}")
print("-"*65)
for l in lotes:
    quants = env['stock.quant'].search([('lot_id','=',l.id)])
    qty = sum(q.quantity for q in quants)
    prov = l.factory_lot_id.name if l.factory_lot_id else '(sin prov)'
    cad = l.expiration_date.strftime('%d/%m/%Y') if l.expiration_date else '---'
    print(f"{l.name:<16} {prov:<20} {cad:<14} {qty}")
