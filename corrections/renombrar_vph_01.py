# -*- coding: utf-8 -*-
# Corrige la orden VPH confirmada 0726/11/VPH -> 0726/01/VPH (primera del mes,
# pedido de Fernando 2026-07-13). El lote esta limpio (0 existencia, sin
# produccion), asi que se renombra orden + lote de forma segura. Ademas ajusta
# la secuencia de VPH para que la proxima de julio sea 0726/02/VPH.
MO = env['mrp.production']
Lot = env['stock.lot']

orden = MO.search([('name', '=', '0726/11/VPH')], limit=1)
lote = Lot.search([('name', '=', '0726/11/VPH')], limit=1)
if MO.search_count([('name', '=', '0726/01/VPH')]) or Lot.search_count([('name', '=', '0726/01/VPH')]):
    print("OJO: ya existe algo con 0726/01/VPH -> NO se renombra")
else:
    if orden:
        orden.name = '0726/01/VPH'
        if 'solution_lot_id' in orden._fields:
            orden.solution_lot_id = '0726/01/VPH'
        print("orden %s renombrada -> 0726/01/VPH (estado %s)" % (orden.id, orden.state))
    if lote:
        # verificar que sigue limpio
        n_q = env['stock.quant'].search_count([('lot_id', '=', lote.id), ('quantity', '!=', 0)])
        if n_q:
            print("OJO: el lote tiene existencia (%s) -> NO se renombra el lote" % n_q)
        else:
            lote.name = '0726/01/VPH'
            print("lote %s renombrado -> 0726/01/VPH" % lote.id)
    # ajustar secuencia VPH: proxima = 0726/02
    if orden:
        seq = orden.product_id.product_tmpl_id.mo_sequence_id
        seq.write({'number_next': 2, 'amunet_last_period': '072026'})
        print("secuencia VPH: number_next=2, periodo=072026")

env.cr.commit()
print("LISTO")
