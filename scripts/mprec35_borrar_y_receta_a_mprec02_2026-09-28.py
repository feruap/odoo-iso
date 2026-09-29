"""Acido cloroaurico: una sola clave. La receta pasa a MPREC02 y MPREC35 se borra.

Autorizado por Mery el 28-sep-2026: "se queda el que tiene movimientos, la receta
se mueve a ese mismo, y el otro se borra, para dejar el espacio libre".

EL CASO: dos fichas para el mismo reactivo.

    MPREC02  Acido tetracloro aurico      10 g comprados el 12-jun a Santa Cruz
                                          Biotechnology, 5 g consumidos, 5 g
                                          ajustados el 16-jul. NO estaba en
                                          ninguna receta.
    MPREC35  Acido cloroaurico (HAuCl4)   NI UN MOVIMIENTO, nunca. Era el
                                          componente de SPACL01.

Acido tetracloroaurico, acido cloroaurico y HAuCl4 son el mismo compuesto.

Consecuencia de tenerlo partido: la receta de SPACL01 (Acido cloroaurico 1%)
pedia MPREC35, que nunca tuvo material, mientras el reactivo real entraba y se
consumia como MPREC02. Por eso la cadena nunca corrio de verdad:

    MPREC35 0.1 g + agua tridestilada  ->  SPACL01
    SPACL01 10 ml + SPCDS01 15 ml + agua  ->  SPNPS01 (nanoparticulas)

En produccion no hay ni una orden de SPACL01 ni de SPNPS01. Los 5 g que si se
usaron salieron por solicitud de material, fuera del flujo de produccion. En
staging la orden de SPACL01 (AMP/MO/00066) esta atorada en borrador pidiendo
MPREC35, y las nanoparticulas consumieron un lote ACL01PRUEBA01 cargado a mano.

QUE HACE, en este orden:
  1. La receta de SPACL01 pasa de MPREC35 a MPREC02 (misma cantidad, misma
     unidad: los dos estan en gramos).
  2. Las ordenes en BORRADOR que pedian MPREC35 se pasan a MPREC02. Solo las de
     borrador: una orden ya confirmada no se toca a la ligera.
  3. Se comprueba que no quede NADA apuntando a MPREC35.
  4. Se borra MPREC35 para dejar la clave libre. Se puede borrar sin dejar
     huerfanos justo porque nunca se movio; el historial del reactivo vive todo
     en MPREC02 y no se toca.

Se borra en vez de archivar porque Mery pidio liberar el espacio: archivar deja
la clave ocupada.

Idempotente: si ya esta hecho, no hace nada.
"""

PT = env['product.template'].sudo()
BomLine = env['mrp.bom.line'].sudo()
Move = env['stock.move'].sudo()

VIEJO, NUEVO = 'MPREC35', 'MPREC02'
viejo = PT.with_context(active_test=False).search([('default_code', '=', VIEJO)], limit=1)
nuevo = PT.search([('default_code', '=', NUEVO)], limit=1)

if not viejo:
    print('[ya] %s ya no existe: la clave esta libre' % VIEJO)
else:
    assert nuevo, 'no existe %s, no se puede mover la receta' % NUEVO
    v_prods, n_prod = viejo.product_variant_ids, nuevo.product_variant_id
    assert n_prod, '%s no tiene variante' % NUEVO
    # Los dos en gramos, pero OJO: son dos REGISTROS de unidad distintos que se
    # llaman igual. El sistema tiene dos "g" duplicadas (la 14, que usan 43
    # productos, y la 46, que usan 36) y cada producto quedo colgado de una.
    # Para esta receta da lo mismo -- las dos valen 1 g -- pero la linea se
    # reescribe con la unidad del producto nuevo para que no quede una cantidad
    # expresada en la unidad de otro arbol. El duplicado de unidades es un tema
    # aparte, reportado a Mery el 28-sep-2026.
    assert viejo.uom_id.name == nuevo.uom_id.name, \
        'unidades de verdad distintas (%s vs %s): revisar antes de mover la receta' % (
            viejo.uom_id.name, nuevo.uom_id.name)
    if viejo.uom_id != nuevo.uom_id:
        print('   nota: %s usa la unidad "%s" (id %s) y %s la "%s" (id %s); '
              'equivalen 1 a 1' % (VIEJO, viejo.uom_id.name, viejo.uom_id.id,
                                   NUEVO, nuevo.uom_id.name, nuevo.uom_id.id))

    print('-- 1. recetas --')
    lineas = BomLine.search([('product_id', 'in', v_prods.ids)])
    for l in lineas:
        print('   %-9s receta de %-9s %g %s  ->  %s' % (
            VIEJO, l.bom_id.product_tmpl_id.default_code, l.product_qty,
            l.product_uom_id.name, NUEVO))
        l.write({'product_id': n_prod.id, 'product_uom_id': nuevo.uom_id.id})
    if not lineas:
        print('   ninguna receta lo usaba ya')

    print('-- 2. ordenes en borrador --')
    moves = Move.search([('product_id', 'in', v_prods.ids)])
    for m in moves:
        orden = m.raw_material_production_id
        if orden and orden.state == 'draft':
            print('   %s (borrador): componente %s -> %s' % (orden.name, VIEJO, NUEVO))
            m.write({'product_id': n_prod.id, 'product_uom': nuevo.uom_id.id})
        else:
            print('   OJO: movimiento %s en estado %s (orden %s) -- NO se toca' % (
                m.id, m.state, orden.name if orden else '-'))
    if not moves:
        print('   ningun movimiento lo usaba')

    print('-- 3. que queda apuntando a %s --' % VIEJO)
    pend = []
    for etiqueta, modelo, dom in (
            ('movimientos', 'stock.move', [('product_id', 'in', v_prods.ids)]),
            ('lineas de movimiento', 'stock.move.line', [('product_id', 'in', v_prods.ids)]),
            ('existencias', 'stock.quant', [('product_id', 'in', v_prods.ids)]),
            ('lotes', 'stock.lot', [('product_id', 'in', v_prods.ids)]),
            ('lineas de receta', 'mrp.bom.line', [('product_id', 'in', v_prods.ids)]),
            ('lineas de compra', 'purchase.order.line', [('product_id', 'in', v_prods.ids)]),
            ('ordenes de produccion', 'mrp.production', [('product_id', 'in', v_prods.ids)]),
    ):
        n = env[modelo].sudo().with_context(active_test=False).search_count(dom)
        print('   %-24s %s' % (etiqueta, n))
        if n:
            pend.append('%s: %s' % (etiqueta, n))

    if pend:
        print('\nNO SE BORRA: todavia apuntan a %s -> %s' % (VIEJO, '; '.join(pend)))
    else:
        print('-- 4. borrar %s --' % VIEJO)
        try:
            viejo.unlink()
            print('   [ok] %s borrado: la clave queda libre para reutilizarse' % VIEJO)
        except Exception as e:
            print('   NO SE PUDO BORRAR: %s' % str(e)[:200])
            print('   (queda intacto; habria que revisar que lo retiene)')

# Comprobacion final
print('\n=== como queda ===')
for clave in (NUEVO, VIEJO):
    t = PT.with_context(active_test=False).search([('default_code', '=', clave)], limit=1)
    print('   %-9s %s' % (clave, t.display_name if t else 'NO EXISTE (clave libre)'))
sp = PT.search([('default_code', '=', 'SPACL01')], limit=1)
for b in env['mrp.bom'].sudo().search([('product_tmpl_id', '=', sp.id)]):
    for l in b.bom_line_ids:
        print('   receta de SPACL01: %-9s %g %s' % (
            l.product_id.default_code, l.product_qty, l.product_uom_id.name))

env.cr.commit()
