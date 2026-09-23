"""Receta de SPSPA05 - Solucion de pretratamiento para almohadilla intermedia.

Formula dada por Mery el 23-sep-2026: **5% de PVP y 5% de NaOH, el resto agua**.
Por litro: 50 g de PVP (MPREC11) + 50 g de NaOH (MPREC09) + agua tridestilada.

El agua completa el litro contando solo los LIQUIDOS, que es como estan hechas
sus hermanas (en SPSPA02: 996.8 ml de agua + 3.2 ml de HCl = 1000; los gramos
de solido no descuentan volumen). Aqui no hay otro liquido, asi que son
1000 ml de agua.

Idempotente: busca por clave y no duplica lineas.
"""

PT   = env['product.template']
BOM  = env['mrp.bom']
Line = env['mrp.bom.line']
g    = env['uom.uom'].search([('name', '=', 'g')], limit=1)
ml   = env['uom.uom'].search([('name', '=', 'ml')], limit=1)
L    = env['uom.uom'].search([('name', '=', 'L')], limit=1)

COMPONENTES = [
    ('MPREC11',  50.0, g,  'Polivinilpirrolidona (PVP) al 5%'),
    ('MPREC09',  50.0, g,  'Hidroxido de sodio (NaOH) al 5%'),
    ('MPATR01', 1000.0, ml, 'Agua tridestilada, el resto'),
]

sp05 = PT.search([('default_code', '=', 'SPSPA05')], limit=1)
assert sp05, 'No existe SPSPA05; correr primero almohadillas_datos_2026-09-23.py'
assert g and ml and L, 'Faltan unidades g / ml / L'

bom = BOM.search([('product_tmpl_id', '=', sp05.id)], limit=1)
if bom:
    print('La receta ya existe (id=%s); se revisan sus lineas.' % bom.id)
else:
    molde = BOM.search([('product_tmpl_id.default_code', '=', 'SPSPA04')], limit=1)
    bom = BOM.create({
        'product_tmpl_id': sp05.id,
        'product_qty': 1.0,
        'product_uom_id': L.id,
        'type': 'normal',
        'consumption': molde.consumption if molde else 'warning',
    })
    print('Receta creada (id=%s): produce 1 L' % bom.id)

faltantes = []
for code, qty, uom, nota in COMPONENTES:
    comp = env['product.product'].search([('default_code', '=', code)], limit=1)
    if not comp:
        faltantes.append(code)
        continue
    linea = bom.bom_line_ids.filtered(lambda l: l.product_id == comp)
    if linea:
        linea.write({'product_qty': qty, 'product_uom_id': uom.id})
        print('  %-9s %8.1f %-3s  actualizada  (%s)' % (code, qty, uom.name, nota))
    else:
        Line.create({'bom_id': bom.id, 'product_id': comp.id,
                     'product_qty': qty, 'product_uom_id': uom.id})
        print('  %-9s %8.1f %-3s  agregada     (%s)' % (code, qty, uom.name, nota))

if faltantes:
    print('\nFALTANTES, no se guardo nada:')
    for f in faltantes:
        print('   ', f)
else:
    env.cr.commit()
    print('\nOK: receta guardada.')
