# -*- coding: utf-8 -*-
"""Pone el ENVASE en las recetas de reenvase de los reactivos PTREC04-13.

Las 23 recetas (una por presentacion) solo consumian el granel. Faltaba el
frasco, que en estos productos NO es empaque posterior: reenvasar ES meter el
polvo en el frasco. Sin el envase en la receta, Odoo no puede decir si alcanza
para producir. Decision de Mery, 22-sep-2026.

El envase se elige por VOLUMEN, no por peso: 100 g de polvo no caben en 100 ml.

    1 g,  5 g  -> COENV06  Envase transparente 30 ml
   10 g, 25 g  -> COENV03  Envase blanco 100 ml
   100 g       -> COENV14  Envase para reactivo 250 ml
   250 g       -> COENV15  Envase para reactivo 500 ml
   500 g       -> COENV16  Envase para reactivo 1 L

Ademas corrige MPREC27 TCEP-HCl, que estaba en Units en vez de gramos: sus
recetas decian "10 unidades de TCEP" en vez de "10 gramos". Se hace ahora
porque el producto esta limpio (cero existencia, movimientos, lotes y compras);
con movimientos, Odoo ya no deja cambiar la unidad.

Correr con:
  /opt/odoo/scripts/run_correction.sh production reenvase_ptrec_envases_2026-09-22.py
"""
import re

ENVASE = {
    '1g': 'COENV06', '5g': 'COENV06',
    '10g': 'COENV03', '25g': 'COENV03',
    '100g': 'COENV14', '250g': 'COENV15', '500g': 'COENV16',
}

B = env['mrp.bom']
P = env['product.product']

# --- 1. TCEP-HCl a gramos, antes de tocar las recetas ---
t27 = env['product.template'].search([('default_code', '=', 'MPREC27')], limit=1)
if t27 and t27.uom_id.name != 'g':
    p27 = P.search([('product_tmpl_id', '=', t27.id)], limit=1)
    sucio = (env['stock.move'].search_count([('product_id', '=', p27.id)])
             or env['stock.lot'].search_count([('product_id', '=', p27.id)])
             or env['purchase.order.line'].search_count([('product_id', '=', p27.id)]))
    if sucio:
        print('MPREC27: NO se cambia la unidad, ya tiene movimientos. Revisar a mano.')
    else:
        g = env['uom.uom'].search([('name', '=', 'g')], limit=1)
        print('MPREC27 TCEP-HCl: %s -> %s' % (t27.uom_id.name, g.name))
        t27.write({'uom_id': g.id})
        env.cr.commit()
else:
    print('MPREC27: ya estaba en %s' % (t27.uom_id.name if t27 else '?'))

# --- 2. el envase en cada receta ---
puestos = ya = 0
sin_identificar = []
for bom in B.search([('code', '=like', 'REENVASE-%')], order='code'):
    m = re.search(r'-(\d+g)$', bom.code or '')
    clave = ENVASE.get(m.group(1)) if m else None
    if not clave:
        sin_identificar.append(bom.code)
        continue
    envase = P.search([('default_code', '=', clave)], limit=1)
    if not envase:
        sin_identificar.append('%s (falta %s)' % (bom.code, clave))
        continue
    if any(l.product_id == envase for l in bom.bom_line_ids):
        ya += 1
        continue
    bom.write({'bom_line_ids': [(0, 0, {
        'product_id': envase.id,
        'product_qty': 1.0,
        'product_uom_id': envase.uom_id.id,
    })]})
    puestos += 1

print('\nenvase agregado a %d recetas | ya lo tenian: %d' % (puestos, ya))
if sin_identificar:
    print('SIN IDENTIFICAR: %s' % sin_identificar)

# --- 3. unidades de los renglones de granel ---
g = env['uom.uom'].search([('name', '=', 'g')], limit=1)
arreglados = 0
for bom in B.search([('code', '=like', 'REENVASE-%')]):
    for l in bom.bom_line_ids:
        if l.product_id.default_code.startswith('COENV'):
            continue
        if l.product_uom_id.name != 'g' and l.product_id.uom_id.name == 'g':
            l.write({'product_uom_id': g.id})
            arreglados += 1
if arreglados:
    print('renglones de granel corregidos a gramos: %d' % arreglados)

# --- verificacion ---
print('\n=== como quedaron ===')
raras = []
for bom in B.search([('code', '=like', 'REENVASE-%')], order='code'):
    comps = ' + '.join('%s %s %s' % (l.product_id.default_code, l.product_qty,
                                     l.product_uom_id.name)
                       for l in bom.bom_line_ids)
    print('  %-26s -> %s' % (bom.code, comps))
    for l in bom.bom_line_ids:
        esperado = 'Units' if l.product_id.default_code.startswith('COENV') else 'g'
        if l.product_uom_id.name != esperado:
            raras.append('%s: %s en %s' % (bom.code, l.product_id.default_code,
                                           l.product_uom_id.name))
print('\nrenglones con unidad rara: %s' % (raras or 'NINGUNO'))

env.cr.commit()
