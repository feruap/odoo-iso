# -*- coding: utf-8 -*-
# Ajusta la orden de solucion que Fernando trabaja actualmente (id 62): su folio
# quedo con la secuencia generica AMP/MO/00019 porque se creo ANTES del fix que
# hace que el folio de las soluciones sea el numero codificado (DDMMYY-NN).
# Esta en borrador, asi que se renombra al numero ya generado en solution_lot_id.
# Pedido de Fernando 2026-07-13.
MO = env['mrp.production']
m = MO.browse(62)
if not m.exists():
    print("La orden 62 no existe");
else:
    print("Antes -> name:", m.name, "| state:", m.state,
          "| solution_lot_id:", m.solution_lot_id,
          "| es_solucion:", m.amunet_is_solution_product)
    if m.state != 'draft':
        print("OJO: la orden NO esta en borrador -> NO se renombra")
    elif not m.amunet_is_solution_product:
        print("OJO: la orden no es de solucion -> NO se renombra")
    elif not m.solution_lot_id:
        print("OJO: no hay numero codificado en solution_lot_id -> NO se renombra")
    elif MO.search_count([('name', '=', m.solution_lot_id), ('id', '!=', m.id)]):
        print("OJO: ya existe otra orden con nombre %s -> NO se renombra" % m.solution_lot_id)
    else:
        nuevo = m.solution_lot_id
        m.name = nuevo
        print("Despues -> name:", m.name)
    env.cr.commit()
print("LISTO")
