# -*- coding: utf-8 -*-
"""Marca como INTERNAS dos soluciones mas.

Interna quiere decir que se queda en el area de fabricacion: se produce a
ARU/Stock en vez de entregarse a Almacen, y cuando otra receta la usa se toma
de la mesa en vez de pedirla.

Revisado con Mery el 21-sep-2026 sobre el catalogo completo:

  SPSHS01  Hidroxido de Sodio 1 M   -- ya estaba marcada, se deja igual
  SPSRB01  Reactivo de Bradford     -- se marca ahora

A ninguna de las dos la consume otra receta, asi que el cambio solo mueve
donde se guarda: NINGUNA receta cambia lo que pide. Verificado comparando el
surtido de las 58 recetas antes y despues.

Correr con:
  /opt/odoo/scripts/run_correction.sh production soluciones_internas_2026-09-21.py
"""

CLAVES = ['SPSHS01', 'SPSRB01']

T = env['product.template']
MO = env['mrp.production']


def foto():
    """Donde se produce cada solucion y que pide su receta."""
    res = {}
    for t in T.search([('categ_id.complete_name', 'ilike', 'soluc')]):
        p = env['product.product'].search([('product_tmpl_id', '=', t.id)], limit=1)
        try:
            m = MO.new({'product_id': p.id})
            m._compute_locations()
            dest = m.location_dest_id.complete_name
        except Exception:
            dest = '?'
        bom = env['mrp.bom'].search([('product_tmpl_id', '=', t.id)], limit=1)
        pide = []
        for l in bom.bom_line_ids:
            pt = l.product_id.product_tmpl_id
            r = pt.amunet_resguardo_aru
            if r == 'no':
                nec = True
            elif r == 'si' or pt.amunet_solucion_interna:
                nec = False
            else:
                c = pt.categ_id
                nec = not (c._amunet_routes_to_aru()
                           if hasattr(c, '_amunet_routes_to_aru') else False)
            if nec:
                pide.append(l.product_id.default_code)
        res[t.default_code] = (dest, tuple(sorted(pide)))
    return res


antes = foto()
for c in CLAVES:
    t = T.search([('default_code', '=', c)], limit=1)
    if not t:
        print('%-10s *** NO EXISTE ***' % c)
        continue
    print('%-10s %-38s interna antes=%s' % (c, (t.name or '')[:36],
                                            t.amunet_solucion_interna))
    t.amunet_solucion_interna = True
despues = foto()

print('\n--- CAMBIOS DE DESTINO ---')
for k in sorted(antes):
    if antes[k][0] != despues[k][0]:
        print('   %-10s %s -> %s' % (k, antes[k][0], despues[k][0]))

print('\n--- CAMBIOS EN EL SURTIDO DE ALGUNA RECETA ---')
hubo = False
for k in sorted(antes):
    if antes[k][1] != despues[k][1]:
        hubo = True
        print('   %-10s antes pedia %s -> ahora %s' % (
            k, list(antes[k][1]), list(despues[k][1])))
if not hubo:
    print('   NINGUNO: ninguna receta cambio lo que pide')

internas = T.search([('categ_id.complete_name', 'ilike', 'soluc'),
                     ('amunet_solucion_interna', '=', True)])
print('\nsoluciones internas ahora: %d -- %s' % (
    len(internas), ', '.join(sorted(internas.mapped('default_code')))))

env.cr.commit()
