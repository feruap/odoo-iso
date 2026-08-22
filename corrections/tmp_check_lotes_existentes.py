for codigo in ['MPREC04','MPREC12','MPREC19','MPREC37','MPREC61']:
    tmpl = env['product.template'].search([('default_code','=',codigo)], limit=1)
    prod = tmpl.product_variant_ids[:1]
    lotes = env['stock.lot'].search([('product_id','=',prod.id)])
    uom = tmpl.uom_id.name
    print(f"\n{codigo} — {tmpl.name} (UoM: {uom})")
    if lotes:
        for l in lotes:
            print(f"  Lote: {l.name} | Prov: {l.factory_lot_id.name if l.factory_lot_id else '?'} | Cad: {l.expiration_date}")
    else:
        print("  Sin lotes registrados")
