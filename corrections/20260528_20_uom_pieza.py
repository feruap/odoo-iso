# Idempotente: crea UoM "Pieza de hoja maestra" (30 cm = 300 mm)
pieza = env['uom.uom'].search([('name','=','Pieza de hoja maestra')], limit=1)
if not pieza:
    cm = env['uom.uom'].search([('name','=','cm')], limit=1)
    pieza = env['uom.uom'].create({
        'name':'Pieza de hoja maestra',
        'factor':300.0, 'relative_factor':30.0,
        'relative_uom_id':cm.id, 'rounding':1.0,
    })
    env.cr.commit()
    print(f"  CREADA Pieza de hoja maestra id={pieza.id}")
else:
    print(f"  YA OK Pieza id={pieza.id}")

# Asignar como UoM alternativa a todas las SPHM
count=0
for h in env['product.template'].search([('default_code','=like','SPHM%')]):
    if pieza not in h.uom_ids:
        h.uom_ids = [(4, pieza.id)]; count+=1
env.cr.commit()
print(f"  uom_ids actualizada en {count} SPHMs")
