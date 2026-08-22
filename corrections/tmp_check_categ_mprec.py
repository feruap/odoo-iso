p = env['product.template'].search([('default_code','=','MPREC04')], limit=1)
print(f"Categoría: {p.categ_id.complete_name} (id={p.categ_id.id})")
print(f"UoM: {p.uom_id.name} (id={p.uom_id.id})")
print(f"tracking={p.tracking}, use_expiration_date={p.use_expiration_date}, amunet_requires_quarantine={p.amunet_requires_quarantine}")
