# -*- coding: utf-8 -*-
"""Da de alta la receta base de las hojas maestras.

NINGUNA de las hojas maestras tenia lista de materiales. Por eso Odoo no podia
saber si hay con que laminar, y el sistema de compras de material productivo se
quedaba ciego justo en los productos que mas se venden (lo levanto Fernando el
21-sep-2026 revisando la compra P00222: el combo respiratorio con 0.4 meses de
cobertura y sin forma de saber si hay insumos).

Esta receta es el ESQUELETO COMUN de toda hoja laminada:

    1 hoja maestra = 30 cm
        MPTS01    Tarjeta de soporte de 6x30cm     1 pieza
        SPALMA11  Almohadilla A11 (absorbente)     1 pieza

Falta la parte que da identidad a cada prueba -- membrana, conjugado y
anticuerpos -- que se define con Ensayo hoja por hoja.

La almohadilla A11 se pone en TODAS por ahora (decision de Mery, 21-sep-2026);
los casos que lleven otra (A10, A12) se ajustan despues.

No pisa nada: salta las hojas que ya tengan receta.

Correr con:
  /opt/odoo/scripts/run_correction.sh production hojas_maestras_bom_soporte_2026-09-21.py
"""

T = env['product.template']
B = env['mrp.bom']
P = env['product.product']

tarjeta = P.search([('default_code', '=', 'MPTS01')], limit=1)
almohadilla = P.search([('default_code', '=', 'SPALMA11')], limit=1)
if not (tarjeta and almohadilla):
    print('FALTA un componente: MPTS01=%s SPALMA11=%s' % (
        bool(tarjeta), bool(almohadilla)))
else:
    print('tarjeta    : %s %s (%s)' % (
        tarjeta.default_code, tarjeta.name, tarjeta.uom_id.name))
    print('almohadilla: %s %s (%s)\n' % (
        almohadilla.default_code, almohadilla.name, almohadilla.uom_id.name))

    hojas = T.search(['|', ('default_code', '=like', 'SPHMC%'),
                      ('default_code', '=like', 'SPHMT%')], order='default_code')
    creadas = saltadas = 0
    for t in hojas:
        if B.search_count([('product_tmpl_id', '=', t.id)]):
            saltadas += 1
            continue
        if t.uom_id.name != 'cm':
            print('  %-10s se salta: su unidad es %s, no cm' % (
                t.default_code, t.uom_id.name))
            saltadas += 1
            continue
        B.create({
            'product_tmpl_id': t.id,
            'product_qty': 30.0,
            'product_uom_id': t.uom_id.id,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {'product_id': tarjeta.id, 'product_qty': 1.0,
                        'product_uom_id': tarjeta.uom_id.id}),
                (0, 0, {'product_id': almohadilla.id, 'product_qty': 1.0,
                        'product_uom_id': almohadilla.uom_id.id}),
            ],
        })
        creadas += 1

    print('\nrecetas creadas: %d | ya tenian o se saltaron: %d' % (
        creadas, saltadas))
    con = [t for t in hojas if B.search_count([('product_tmpl_id', '=', t.id)])]
    print('hojas maestras con receta: %d de %d' % (len(con), len(hojas)))
    if con:
        b = B.search([('product_tmpl_id', '=', con[0].id)], limit=1)
        print('\nejemplo %s: produce %s %s' % (
            con[0].default_code, b.product_qty, b.product_uom_id.name))
        for l in b.bom_line_ids:
            print('   %-10s %-38s %s %s' % (
                l.product_id.default_code, (l.product_id.name or '')[:36],
                l.product_qty, l.product_uom_id.name))

env.cr.commit()
