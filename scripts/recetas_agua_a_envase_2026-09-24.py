# -*- coding: utf-8 -*-
"""Las recetas piden el agua en la unidad de almacen, no en mililitros.

EL PROBLEMA. Las tres aguas -- bidestilada, destilada y tridestilada -- se
compran, se guardan y se entregan por garrafon de 20 L: el producto se mide en
Units. Las recetas las pedian en MILILITROS, que es lo que se ocupa en la mesa.
Units y ml son categorias de unidad distintas, asi que ninguna de esas recetas
se podia fabricar: el preflight bloqueaba comparando mililitros contra
garrafones ("requiere 980.000 ml, disponible 22.000").

LA SOLUCION, ya probada en SPNPS01. La receta pide la fraccion de garrafon y el
operador anota los mililitros que uso; la columna "Por consumir" le muestra
mililitros, nunca la fraccion. Aqui se aplica al resto de las recetas.

Se deja la equivalencia escrita en la nota de cada BoM, para que cualquiera que
abra la receta sepa cuantos mililitros son sin hacer la cuenta.

No se tocan los BoM de los productos .ml -- MPABI01.ml, MPADE01.ml y
MPATR01.ml -- que son las recetas de conversion del garrafon y ya estan en la
unidad correcta.

IDEMPOTENTE: una linea que ya esta en la unidad de almacen se salta.

FALTA UN PASO al correrlo: las ordenes ya abiertas siguen pidiendo mililitros,
porque el preflight y la reserva validan move_raw_ids de la orden y no la
receta. Hay que alinearlas aparte (en staging fue AMP/MO/00035).

REDONDEO: con la precision "Product Unit" en 4 decimales, ocho de las 29
recetas se mueven hasta 1 ml en 1 L (0.14% como maximo). Si eso no se acepta,
la precision tiene que subir a 6 decimales ANTES de correr esto.

Corrido en staging el 24-sep-2026: 29 convertidas, 4 saltadas.
"""
prec = env['decimal.precision'].sudo().precision_get('Product Unit')
tmpls = env['product.template'].sudo().search([('amunet_contenido_envase','>',0)])
ids = tmpls.mapped('product_variant_ids').ids
lineas = env['mrp.bom.line'].sudo().search([('product_id','in',ids)])

hechas, saltadas = [], []
for l in lineas.sorted(lambda x: x.bom_id.product_tmpl_id.default_code or ''):
    t = l.product_id.product_tmpl_id
    if l.product_uom_id.id == t.uom_id.id:
        saltadas.append((l.bom_id.product_tmpl_id.default_code, 'ya en %s' % t.uom_id.name))
        continue
    if l.product_uom_id.id != t.amunet_uom_consumo_id.id:
        saltadas.append((l.bom_id.product_tmpl_id.default_code,
                         'unidad inesperada: %s' % l.product_uom_id.name))
        continue
    ml = l.product_qty
    frac = round(ml / t.amunet_contenido_envase, prec)
    if not frac:
        saltadas.append((l.bom_id.product_tmpl_id.default_code, 'se volveria cero'))
        continue
    l.write({'product_uom_id': t.uom_id.id, 'product_qty': frac})
    hechas.append((l.bom_id, t, ml, frac))

print('   convertidas: %s     saltadas: %s' % (len(hechas), len(saltadas)))
print('')
for bom, t, ml, frac in hechas:
    print('   %-10s %-12s %8.2f ml -> %.4f %s' % (
        bom.product_tmpl_id.default_code, t.default_code, ml, frac, t.uom_id.name))
print('')
for cod, motivo in saltadas:
    print('   saltada: %-14s %s' % (cod, motivo))

# nota en cada BoM, sin borrar lo que ya hubiera
for bom, t, ml, frac in hechas:
    texto = ('%s: %.0f %s por lote de %s %s. Se almacena por garrafón de %.0f %s, '
             'así que la receta la pide como %.4f %s; al fabricar, el operador '
             'anota los %.0f %s que usó y el sistema descuenta la fracción del '
             'garrafón.' % (t.name, ml, t.amunet_uom_consumo_id.name,
                           bom.product_qty, bom.product_uom_id.name,
                           t.amunet_contenido_envase, t.amunet_uom_consumo_id.name,
                           frac, t.uom_id.name, ml, t.amunet_uom_consumo_id.name))
    if 'note' in bom._fields:
        previo = (bom.note or '').strip()
        if texto not in previo:
            bom.note = (previo + '\n\n' + texto).strip() if previo else texto
env.flush_all(); env.cr.commit()
print('')
print('   nota de equivalencia escrita en %s recetas' % len(hechas))
