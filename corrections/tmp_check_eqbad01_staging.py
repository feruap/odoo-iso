p = env['product.template'].search([('default_code','=','EQBAD01')], limit=1)
print(f"id={p.id} nombre={p.name}")
print(f"categ={p.categ_id.complete_name}")
print(f"tracking={p.tracking}")
print(f"use_expiration_date={p.use_expiration_date}")
print(f"amunet_requires_quarantine={p.amunet_requires_quarantine}")
prod = p.product_variant_ids[:1]
seq = prod.lot_sequence_id
print(f"secuencia={seq.prefix if seq else 'NINGUNA'}")
