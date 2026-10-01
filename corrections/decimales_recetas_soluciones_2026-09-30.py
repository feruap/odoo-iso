# -*- coding: utf-8 -*-
"""Los 7 numeros que Mery marco en negritas en el archivo de soluciones.

DE DONDE SALEN. Archivo "Soluciones_a_probar_2026-09-28mery.xlsx" que Mery
devolvio por Discuss el 30-sep-2026 (adjunto 11115 en staging). Las negritas
estan todas en la columna Cantidad: son los valores que deben quedar, contra
los que el sistema tenia.

DOS COSAS DISTINTAS EN LAS 7 MARCAS:

1. CINCO SON PRECISION. El sistema los tenia recortados a 2 decimales porque
   43 campos del codigo pedian la precision con el nombre VIEJO de Odoo
   ('Product Unit of Measure'), que en Odoo 19 se llama 'Product Unit'. Odoo no
   lo encontraba, caia a su default de 2 y redondeaba EN SILENCIO. Corregido
   aparte; sin eso este script no serviria de nada porque los valores se
   volverian a recortar al guardar.
   No son decimales de adorno: 8.766 g/L de NaCl son EXACTAMENTE 150 mM
   (58.44 g/mol x 0.15). 2.434 g/L de Tris-base son ~20 mM.

2. DOS SON CAMBIOS DE FONDO.
   - SPLPT01, el PBS 10X pasa de 10 a 100 ml. Corrige un error de
     concentracion: una solucion de lavado debe quedar en 1X, y 10 ml de un
     concentrado 10X en un litro dan 0.1X -- diez veces mas diluida. Con 100 ml
     queda 1X.
     OJO: con esto la receta suma 1,090.5 ml para un lote de 1 L. El agua
     tendria que bajar de 0.0495 a 0.045 garrafones (899.5 ml) para que cierre.
     NO se toca aqui: Mery marco el PBS, no el agua, y cambiar una cantidad que
     ella no marco seria decidir por ella en una formulacion. Queda avisado.
   - SPSAG01, el NaOH 20% pasa de 7 a 9 ml. El volumen casi no se mueve
     (1,000 -> 1,002 ml).

NINGUNA de las 5 soluciones tiene ordenes abiertas. Los cambios de decimales no
alteran lo que consumen los 19 conjugados, los 3 viales ni las 2 almohadillas
que dependen de ellas: la cantidad que el consumidor pide no cambia.

Idempotente.
"""
CAMBIOS = [
    # (solucion, componente, valor_nuevo, unidad_esperada, nota)
    ('SPLPT01', 'SPPBS02', 100.0,   'ml', 'PBS 10X: de 0.1X a 1X'),
    ('SPSAG01', 'MPREC05', 8.766,   'g',  'NaCl exactamente 150 mM'),
    ('SPSAG01', 'MPREC06', 4.7175,  'g',  'Triton X-100'),
    ('SPSAG01', 'SPSHS02', 9.0,     'ml', 'NaOH 20%'),
    ('SPSDC01', 'MPREC10', 2.434,   'g',  'Tris-base ~20 mM'),
    ('SPSDC02', 'MPREC10', 2.434,   'g',  'Tris-base ~20 mM'),
    ('SPSPA01', 'MPREC12', 0.465,   'ml', 'Tween 20'),
]

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

aplicados, ya_estaban, problemas = [], [], []
for clave, comp, nuevo, uom_esp, nota in CAMBIOS:
    p = env['product.product'].search([('default_code', '=', clave)], limit=1)
    if not p:
        problemas.append((clave, comp, 'no existe la solucion')); continue
    boms = env['mrp.bom'].search([('product_tmpl_id', '=', p.product_tmpl_id.id)])
    if len(boms) != 1:
        problemas.append((clave, comp, '%d recetas' % len(boms))); continue
    lineas = boms.bom_line_ids.filtered(lambda l: l.product_id.default_code == comp)
    if len(lineas) != 1:
        problemas.append((clave, comp, '%d renglones' % len(lineas))); continue
    l = lineas[0]
    # La unidad tiene que ser la que esperabamos: si cambio, el numero ya no
    # significa lo mismo y no se toca a ciegas.
    uom_real = l.product_uom_id.name
    if uom_real != uom_esp:
        problemas.append((clave, comp, 'unidad %s, esperaba %s' % (uom_real, uom_esp)))
        continue
    antes = l.product_qty
    if abs(antes - nuevo) < 1e-9:
        ya_estaban.append((clave, comp, nuevo)); continue
    l.write({'product_qty': nuevo})
    l.flush_recordset()
    l.invalidate_recordset()
    aplicados.append((clave, comp, antes, nuevo, l.product_qty, uom_real, nota))

env.cr.commit()

print('=' * 96)
print('APLICADOS: %d' % len(aplicados))
for clave, comp, antes, nuevo, quedo, uom, nota in aplicados:
    aviso = '' if abs(quedo - nuevo) < 1e-9 else '   <<< SE RECORTO A %s' % quedo
    print('   %-9s %-9s %10s -> %-10s %-4s  %s%s' % (
        clave, comp, antes, nuevo, uom, nota, aviso))
print('-' * 96)
print('YA ESTABAN: %d  %s' % (len(ya_estaban),
      ', '.join('%s/%s' % (c, k) for c, k, _ in ya_estaban) or '-'))
if problemas:
    print('-' * 96)
    print('NO SE TOCARON:')
    for clave, comp, motivo in problemas:
        print('   %-9s %-9s %s' % (clave, comp, motivo))
print('-' * 96)
print('COMO QUEDAN LAS 5 RECETAS:')
for clave in ('SPLPT01', 'SPSAG01', 'SPSDC01', 'SPSDC02', 'SPSPA01'):
    p = env['product.product'].search([('default_code', '=', clave)], limit=1)
    b = env['mrp.bom'].search([('product_tmpl_id', '=', p.product_tmpl_id.id)], limit=1)
    print('   %s  produce %s %s' % (clave, b.product_qty, b.product_uom_id.name))
    for l in b.bom_line_ids.sorted(lambda x: x.product_id.default_code or ''):
        print('      %-9s %12s %s' % (l.product_id.default_code, l.product_qty,
                                      l.product_uom_id.name))
print('=' * 96)
