# -*- coding: utf-8 -*-
"""Alta de SPCPR01 - Solucion de Corrimiento PCR rapida.

Pedido por Mery (25-sep-2026): receta igual al PBS/Tween, 2.5 anos de caducidad,
se entrega a almacen y si requiere analisis de calidad.

La receta se calca de SPLPT01 'Solucion de Lavado (PBS/Tween)', que es la unica
del catalogo con PBS y Tween:
    SPPBS02  PBS 10X      10 ml
    MPREC12  Tween 20     0.5 ml
    MPATR01  Agua tridestilada  990 ml  (0.0495 garrafones)

El producto se calca de SPLPT01 para heredar categoria, unidad, rutas y
configuracion de solucion, y se le cambia nombre, clave y caducidad.

CLAVE PROPUESTA: SPCPR01 (SP semiprocesado + CPR corrimiento PCR + 01). Falta
que DOCUMENTACION la libere, que es quien lleva el control de claves.

Idempotente: si ya existe, no duplica.
"""
PT = env['product.template'].sudo()
P  = env['product.product'].sudo()
BOM = env['mrp.bom'].sudo()

CLAVE  = 'SPCPR01'
NOMBRE = 'Solución de Corrimiento PCR rápida'
CADUCIDAD = '2.5 años'
MOLDE = 'SPLPT01'

molde = PT.search([('default_code','=',MOLDE)], limit=1)
assert molde, 'no encuentro el molde %s' % MOLDE
ya = PT.search([('default_code','=',CLAVE)], limit=1)
if ya:
    print('   %s ya existe: %s' % (CLAVE, ya.name))
    nuevo = ya
else:
    vals = {
        'default_code': CLAVE,
        'name': NOMBRE,
        'type': molde.type,
        'is_storable': molde.is_storable,
        'categ_id': molde.categ_id.id,
        'uom_id': molde.uom_id.id,
        'tracking': molde.tracking,
        'use_expiration_date': molde.use_expiration_date,
        'amunet_expiration_text': CADUCIDAD,
        'amunet_req_quality_control': True,
        'purchase_ok': False,
        'sale_ok': False,
    }
    for extra in ('amunet_solucion_interna','amunet_initial_ph','route_ids'):
        if extra in molde._fields and molde[extra]:
            vals[extra] = [(6,0,molde[extra].ids)] if extra=='route_ids' else molde[extra]
    nuevo = PT.with_context(amunet_alta_autorizada=True).create(vals)
    print('   creado %s: %s' % (CLAVE, nuevo.name))

print('      categoria:  %s' % nuevo.categ_id.complete_name)
print('      unidad:     %s   trazabilidad: %s' % (nuevo.uom_id.name, nuevo.tracking))
print('      caducidad:  %s' % nuevo.amunet_expiration_text)
print('      analisis:   %s' % nuevo.amunet_req_quality_control)

# receta calcada del molde
bom_molde = BOM.search([('product_tmpl_id','=',molde.id)], limit=1)
assert bom_molde, 'el molde no tiene receta'
bom = BOM.search([('product_tmpl_id','=',nuevo.id)], limit=1)
if bom:
    print('   la receta ya existe (%s lineas)' % len(bom.bom_line_ids))
else:
    bom = BOM.create({
        'product_tmpl_id': nuevo.id,
        'product_qty': bom_molde.product_qty,
        'product_uom_id': bom_molde.product_uom_id.id,
        'type': bom_molde.type,
        'code': CLAVE,
        'bom_line_ids': [(0,0,{
            'product_id': l.product_id.id,
            'product_qty': l.product_qty,
            'product_uom_id': l.product_uom_id.id,
        }) for l in bom_molde.bom_line_ids],
    })
    print('   receta creada: produce %s %s' % (bom.product_qty, bom.product_uom_id.name))
for l in bom.bom_line_ids:
    tt = l.product_id.product_tmpl_id
    c = ('%.0f %s' % (l.product_qty*tt.amunet_contenido_envase, tt.amunet_uom_consumo_id.name)) \
        if tt.amunet_contenido_envase else ('%s %s' % (l.product_qty, l.product_uom_id.name))
    print('      %-10s %-14s %s' % (l.product_id.default_code, c, (l.product_id.name or '')[:30]))
env.flush_all(); env.cr.commit()
print('   LISTO')
