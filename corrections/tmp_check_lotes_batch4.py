for codigo in ['MPREC17','MPREC31','MPREC66']:
    tmpl = env['product.template'].search([('default_code','=',codigo)], limit=1)
    prod = tmpl.product_variant_ids[:1]
    lotes = env['stock.lot'].search([('product_id','=',prod.id)], order='name')
    print(f"{codigo} — {tmpl.name}")
    for l in lotes:
        prov = l.factory_lot_id.name if l.factory_lot_id else '(sin prov)'
        print(f"  {l.name} | Prov: {prov}")
    if not lotes:
        print("  Sin lotes")
