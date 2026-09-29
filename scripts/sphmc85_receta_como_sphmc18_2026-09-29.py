"""SPHMC85 (la hoja del combo) queda con la misma receta y ruta que SPHMC18.

Autorizado por Mery el 29-sep-2026: "SPHMC85 es la de combos, debe ser la misma que
para dengue net. completala."

EL CASO: Fernando lo pregunto el 3-sep -- "y la de Dengue IgG/IgM CM (SPHMC85) si
difiere de la 18" -- y quedo sin contestar. La respuesta es que NO difiere, pero en
el sistema estaba a medias:

    SPHMC18   membrana + tarjeta + 6 almohadillas + 2 conjugados   = 10 componentes
              y 9 pasos de ruta
    SPHMC85   tarjeta + una almohadilla                            =  2 componentes
              y NINGUN paso de ruta

Es la hoja de la que entraron 900 cm del combo mosquito el 28-sep, asi que sin receta
ni ruta no se puede laminar ni planear.

QUE HACE: copia de SPHMC18 lo que le falta a SPHMC85 -- componentes y pasos de ruta --
respetando lo que ya tiene. Los dos BoM producen 30 cm, asi que las cantidades se
copian tal cual, sin escalar. En los nombres de los pasos cambia el sufijo para que
digan CM y no se confundan en el piso.

Idempotente.
"""

PT = env['product.template'].sudo()
Bom = env['mrp.bom'].sudo()
Paso = env['mrp.routing.workcenter'].sudo()

origen_t = PT.search([('default_code', '=', 'SPHMC18')], limit=1)
destino_t = PT.search([('default_code', '=', 'SPHMC85')], limit=1)
assert origen_t and destino_t, 'falta SPHMC18 o SPHMC85'
bom_o = Bom.search([('product_tmpl_id', '=', origen_t.id)], limit=1)
bom_d = Bom.search([('product_tmpl_id', '=', destino_t.id)], limit=1)
assert bom_o and bom_d, 'falta el BoM de alguna de las dos'

# Las cantidades se copian tal cual solo si las dos recetas producen lo mismo.
factor = 1.0
if abs(bom_o.product_qty - bom_d.product_qty) > 0.001:
    factor = bom_d.product_qty / bom_o.product_qty
    print('OJO: producen distinto (%g vs %g), las cantidades se escalan x%g' % (
        bom_o.product_qty, bom_d.product_qty, factor))
else:
    print('las dos recetas producen %g %s: las cantidades se copian tal cual' % (
        bom_d.product_qty, bom_d.product_uom_id.name))

print('\n-- componentes --')
ya_tiene = {l.product_id.id: l for l in bom_d.bom_line_ids}
agregados = 0
for l in bom_o.bom_line_ids.sorted(lambda x: x.product_id.default_code or ''):
    clave = l.product_id.default_code
    if l.product_id.id in ya_tiene:
        actual = ya_tiene[l.product_id.id]
        esperada = l.product_qty * factor
        if abs(actual.product_qty - esperada) > 0.0001:
            print('   [ajusta] %-9s %g -> %g %s' % (
                clave, actual.product_qty, esperada, l.product_uom_id.name))
            actual.write({'product_qty': esperada,
                          'product_uom_id': l.product_uom_id.id})
        else:
            print('   [ya]     %-9s %g %s' % (clave, actual.product_qty,
                                              actual.product_uom_id.name))
        continue
    env['mrp.bom.line'].sudo().create({
        'bom_id': bom_d.id, 'product_id': l.product_id.id,
        'product_qty': l.product_qty * factor,
        'product_uom_id': l.product_uom_id.id,
    })
    agregados += 1
    print('   [ok]     %-9s %g %s  (copiado de SPHMC18)' % (
        clave, l.product_qty * factor, l.product_uom_id.name))

print('\n-- pasos de ruta --')
pasos_o = Paso.search([('bom_id', '=', bom_o.id)], order='sequence')
pasos_d = Paso.search([('bom_id', '=', bom_d.id)], order='sequence')
if pasos_d:
    print('   [ya] SPHMC85 ya tiene %s paso(s); no se toca la ruta' % len(pasos_d))
else:
    for p in pasos_o:
        nombre = (p.name or '').replace('Dengue IgG/IgM', 'Dengue IgG/IgM CM')
        Paso.create({
            'bom_id': bom_d.id, 'name': nombre,
            'workcenter_id': p.workcenter_id.id,
            'sequence': p.sequence,
            'time_cycle_manual': p.time_cycle_manual,
        })
        print('   [ok] %3s  %-26s %s' % (p.sequence, p.workcenter_id.name,
                                         nombre[:58]))

bom_d.invalidate_recordset()
print('\n=== como queda SPHMC85 ===')
print('   produce %g %s' % (bom_d.product_qty, bom_d.product_uom_id.name))
for l in bom_d.bom_line_ids.sorted(lambda x: x.product_id.default_code or ''):
    print('   %-9s %10g %-6s %s' % (
        l.product_id.default_code, l.product_qty, l.product_uom_id.name,
        (l.product_id.product_tmpl_id.nombre_etiqueta or l.product_id.name)[:34]))
print('   pasos de ruta: %s' % Paso.search_count([('bom_id', '=', bom_d.id)]))
print('   (SPHMC18 tiene %s componentes y %s pasos)' % (
    len(bom_o.bom_line_ids), len(pasos_o)))
env.cr.commit()
