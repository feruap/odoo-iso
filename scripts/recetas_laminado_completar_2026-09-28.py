# -*- coding: utf-8 -*-
"""Completar las recetas de laminado de las 15 hojas maestras.

Tres cosas, del archivo de Mery y de lo que ya tenia produccion:

1. LA MEMBRANA, que no estaba en ninguna de las 15. Es la capa donde se imprime
   la linea de prueba. MPMNC03 en 11 hojas y MPMNC02 en 4, segun el archivo.

2. SPALMA14 en Influenza (SPHMC15), la unica que usa esa intermedia. Faltaba
   porque el producto se dio de alta el 25-sep, despues de armar las recetas.

3. SPALMA12, LA ABSORBENTE. Produccion la tiene en las 15 recetas y staging la
   perdio: quien armo las capas nuevas borro la linea que ya existia. Sin esto,
   promover staging dejaria a las 15 hojas de produccion sin absorbente.
   (La absorbente NO es MPAAB01 -- ese solo se usa en 2 recetas ajenas -- es
   SPALMA12, la pretratada, usada en 93 recetas de produccion.)

Cantidades: 1 unidad por hoja de 30 cm, igual que el resto de las capas.
Idempotente: no duplica una linea que ya exista.
"""
P = env['product.product'].sudo()
Line = env['mrp.bom.line'].sudo()
MEMBRANA = {
 'SPHMC01':'MPMNC02','SPHMC18':'MPMNC03','SPHMC19':'MPMNC03','SPHMC15':'MPMNC03',
 'SPHMC24':'MPMNC03','SPHMC38':'MPMNC03','SPHMC20':'MPMNC02','SPHMC22':'MPMNC03',
 'SPHMC23':'MPMNC03','SPHMC09':'MPMNC03','SPHMT01':'MPMNC02','SPHMC07':'MPMNC03',
 'SPHMC45':'MPMNC02','SPHMC37':'MPMNC03','SPHMC52':'MPMNC03',
}
EXTRA = {'SPHMC15': ['SPALMA14']}
ABSORBENTE = 'SPALMA12'

def agregar(bom, cod, etiqueta):
    p = P.search([('default_code','=',cod)], limit=1)
    if not p:
        print('         %-10s NO EXISTE el producto' % cod); return 0
    if p.id in bom.bom_line_ids.mapped('product_id').ids:
        return 0
    Line.create({'bom_id': bom.id, 'product_id': p.id,
                 'product_qty': 1.0, 'product_uom_id': p.uom_id.id})
    print('         + %-10s %-14s %s' % (cod, etiqueta, (p.name or '')[:34]))
    return 1

tot = 0
for cod, memb in MEMBRANA.items():
    p = P.search([('default_code','=',cod)], limit=1)
    bom = env['mrp.bom'].sudo().search([('product_tmpl_id','=',p.product_tmpl_id.id)], limit=1)
    if not bom: print('   %-10s sin BoM' % cod); continue
    print('   %-10s %s' % (cod, (p.name or '').replace('Hoja Maestra ','')[:28]))
    n = agregar(bom, memb, 'membrana')
    n += agregar(bom, ABSORBENTE, 'absorbente')
    for e in EXTRA.get(cod, []):
        n += agregar(bom, e, 'intermedia')
    if n == 0: print('         (ya estaba completa)')
    tot += n
env.flush_all(); env.cr.commit()
print('')
print('   lineas agregadas: %s' % tot)
print('')
print('   === como quedan (2 de muestra):')
for cod in ('SPHMC18','SPHMC15'):
    p = P.search([('default_code','=',cod)], limit=1)
    bom = env['mrp.bom'].sudo().search([('product_tmpl_id','=',p.product_tmpl_id.id)], limit=1)
    print('      %s  %s lineas:' % (cod, len(bom.bom_line_ids)))
    for l in bom.bom_line_ids.sorted(lambda x: x.product_id.default_code or ''):
        print('         %-10s %s %s' % (l.product_id.default_code, l.product_qty, l.product_uom_id.name))
