for codigo in ['MPREC20','MPREC21','MPREC32','MPREC63','MPREC17']:
    tmpl = env['product.template'].search([('default_code','=',codigo)], limit=1)
    prod = tmpl.product_variant_ids[:1]
    lotes = env['stock.lot'].search([('product_id','=',prod.id)])
    print(f"{codigo} — {tmpl.name} (UoM: {tmpl.uom_id.name})")
    if lotes:
        for l in lotes:
            print(f"  Lote: {l.name} | Prov: {l.factory_lot_id.name if l.factory_lot_id else '?'}")
    else:
        print("  Sin lotes")
