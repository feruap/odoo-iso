"""Revisa categorías de consumibles y UoM piezas."""
categs = env['product.category'].search([('complete_name','ilike','consumible')], order='complete_name')
for c in categs:
    print(f"  id={c.id} | {c.complete_name}")
print()
uom = env['uom.uom'].search([('name','ilike','unit'),('category_id.name','ilike','unit')], limit=3)
for u in uom:
    print(f"  uom id={u.id} | {u.name} | categ={u.category_id.name}")
