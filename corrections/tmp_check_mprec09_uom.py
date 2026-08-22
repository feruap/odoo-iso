for c in ['MPREC09']:
    p = env['product.template'].search([('default_code','=',c)],limit=1)
    print(f"{c} UoM: {p.uom_id.name} (id={p.uom_id.id})")
