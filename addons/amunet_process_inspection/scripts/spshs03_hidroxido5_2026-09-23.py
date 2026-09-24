"""SPSHS03 - Solucion Hidroxido de Sodio al 5%, y correccion de SPSPA05.

Mery, 23-sep-2026: la almohadilla intermedia no lleva sosa pesada al vuelo,
lleva **solucion de hidroxido al 5%**, igual que las demas soluciones usan
soluciones ya formuladas (SPSAC01 HCl 6 M) y no el acido puro.

Ya existian dos concentraciones de hidroxido, ninguna al 5%:
    SPSHS01  Solucion Hidroxido de Sodio 1 M   ->  40 g/L (4%)
    SPSHS02  Hidroxido de sodio 20%            -> 200 g/L
Se agrega la tercera siguiendo el consecutivo de la serie:
    SPSHS03  Solucion Hidroxido de Sodio al 5% ->  50 g/L

Y SPSPA05 deja de consumir el reactivo solido: ahora lleva PVP 50 g (5%) mas
1000 ml de SPSHS03, que aporta el hidroxido al 5%.

CLAVE PENDIENTE DE LIBERACION: SPSHS03 se propone siguiendo la normativa
(SP = semiprocesado, SHS = solucion hidroxido de sodio, 03 = consecutivo).
Falta la confirmacion de Almacen, como manda el procedimiento de alta.

Idempotente: busca por clave y no duplica.
"""

PT   = env['product.template']
BOM  = env['mrp.bom']
Line = env['mrp.bom.line']
g    = env['uom.uom'].search([('name', '=', 'g')], limit=1)
ml   = env['uom.uom'].search([('name', '=', 'ml')], limit=1)
L    = env['uom.uom'].search([('name', '=', 'L')], limit=1)
assert g and ml and L, 'Faltan unidades g / ml / L'

NOMBRE_03 = 'Solución Hidroxido de Sodio al 5%'

# --- 1. Alta de SPSHS03, calcada de SPSHS01 ---------------------------------
print('--- SPSHS03 ---')
sp03 = PT.search([('default_code', '=', 'SPSHS03')], limit=1)
if sp03:
    print('  ya existe')
else:
    molde = PT.search([('default_code', '=', 'SPSHS01')], limit=1)
    assert molde, 'No existe SPSHS01 para usar de molde'
    sp03 = PT.with_context(amunet_alta_autorizada=True).create({
        'default_code': 'SPSHS03',
        'name': NOMBRE_03,
        'type': molde.type,
        'is_storable': molde.is_storable,
        'categ_id': molde.categ_id.id,
        'uom_id': molde.uom_id.id,
        'tracking': molde.tracking,
        'use_expiration_date': molde.use_expiration_date,
        'qc_required': molde.qc_required,
        'amunet_req_quality_control': molde.amunet_req_quality_control,
        'route_ids': [(6, 0, molde.route_ids.ids)],
    })
    sp03.with_context(lang='es_MX').write({'name': NOMBRE_03})
    print('  creado: %s' % sp03.name)

# --- 2. Receta de SPSHS03: 50 g de sosa por litro de agua -------------------
print('--- receta de SPSHS03 ---')
bom03 = BOM.search([('product_tmpl_id', '=', sp03.id)], limit=1)
if not bom03:
    bom03 = BOM.create({'product_tmpl_id': sp03.id, 'product_qty': 1.0,
                        'product_uom_id': L.id, 'type': 'normal',
                        'consumption': 'warning'})
    print('  receta creada, produce 1 L')
for code, qty, uom in (('MPREC09', 50.0, g), ('MPATR01', 1000.0, ml)):
    comp = env['product.product'].search([('default_code', '=', code)], limit=1)
    assert comp, 'No existe %s' % code
    linea = bom03.bom_line_ids.filtered(lambda l: l.product_id == comp)
    if linea:
        linea.write({'product_qty': qty, 'product_uom_id': uom.id})
    else:
        Line.create({'bom_id': bom03.id, 'product_id': comp.id,
                     'product_qty': qty, 'product_uom_id': uom.id})
    print('  %-9s %8.1f %s' % (code, qty, uom.name))

# --- 3. SPSPA05 pasa a consumir la solucion, no el solido -------------------
print('--- SPSPA05 ---')
sp05 = PT.search([('default_code', '=', 'SPSPA05')], limit=1)
assert sp05, 'No existe SPSPA05'
bom05 = BOM.search([('product_tmpl_id', '=', sp05.id)], limit=1)
assert bom05, 'SPSPA05 no tiene receta'

# fuera la sosa pesada y el agua: los dos los aporta ahora SPSHS03
for code in ('MPREC09', 'MPATR01'):
    comp = env['product.product'].search([('default_code', '=', code)], limit=1)
    linea = bom05.bom_line_ids.filtered(lambda l: l.product_id == comp)
    if linea:
        linea.unlink()
        print('  %s retirado (lo aporta SPSHS03)' % code)

for code, qty, uom in (('MPREC11', 50.0, g), ('SPSHS03', 1000.0, ml)):
    comp = env['product.product'].search([('default_code', '=', code)], limit=1)
    assert comp, 'No existe %s' % code
    linea = bom05.bom_line_ids.filtered(lambda l: l.product_id == comp)
    if linea:
        linea.write({'product_qty': qty, 'product_uom_id': uom.id})
        print('  %-9s %8.1f %-3s actualizada' % (code, qty, uom.name))
    else:
        Line.create({'bom_id': bom05.id, 'product_id': comp.id,
                     'product_qty': qty, 'product_uom_id': uom.id})
        print('  %-9s %8.1f %-3s agregada' % (code, qty, uom.name))

env.cr.commit()
print('\nOK: cambios guardados.')
