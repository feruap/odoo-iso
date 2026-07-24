# -*- coding: utf-8 -*-
# LIBERACION DIRECTA de anticuerpos MPANT desde Control de calidad (cuarentena
# de recepcion) a Existencias. Autorizada por Fernando Ruiz (dueno) el
# 2026-07-14 de forma EXCEPCIONAL porque el modulo de Calidad aun no puede
# liberar anticuerpos. Se hace via transferencia interna trazable (tipo 6
# "Almacenamiento" AMP: Control de calidad -> Existencias), NO editando quants
# a mano, para dejar registro (que, cuanto, lotes, quien, cuando).
# PENDIENTE ISO: registrar el analisis retroactivo cuando el modulo este listo.
Picking = env['stock.picking']
Move = env['stock.move']
Quant = env['stock.quant']
SRC = 7    # AMP/Entrada/Control de calidad
DEST = 5   # AMP/Existencias
PTYPE = 6  # Almacenamiento (AMP): Control de calidad -> Existencias

quants = Quant.search([('location_id', '=', SRC), ('quantity', '>', 0)])
quants = quants.filtered(lambda q: (q.product_id.default_code or '').startswith('MPANT'))
print("Lotes MPANT a liberar:", len(quants), "| unidades:", sum(quants.mapped('quantity')))
if not quants:
    print("NADA que liberar")
else:
    picking = Picking.create({
        'picking_type_id': PTYPE, 'location_id': SRC, 'location_dest_id': DEST,
        'origin': 'Liberacion directa MP anticuerpos - autorizada por Fernando Ruiz '
                  '(modulo de Calidad no disponible) 2026-07-14',
    })
    by_prod = {}
    for q in quants:
        by_prod[q.product_id] = by_prod.get(q.product_id, 0.0) + q.quantity
    for prod, qty in by_prod.items():
        Move.create({
            'description_picking': prod.display_name, 'product_id': prod.id,
            'product_uom_qty': qty, 'product_uom': prod.uom_id.id,
            'picking_id': picking.id, 'location_id': SRC, 'location_dest_id': DEST,
        })
    picking.action_confirm()
    picking.action_assign()
    for m in picking.move_ids:
        m.picked = True
    picking.button_validate()
    env.cr.commit()
    print("Picking:", picking.name, "| estado:", picking.state, "| productos:", len(picking.move_ids))
    # Verificacion post
    q_src = Quant.search([('location_id', '=', SRC), ('quantity', '>', 0)]).filtered(
        lambda q: (q.product_id.default_code or '').startswith('MPANT'))
    q_dest = Quant.search([('location_id', '=', DEST), ('quantity', '>', 0)]).filtered(
        lambda q: (q.product_id.default_code or '').startswith('MPANT'))
    print("VERIF: MPANT en cuarentena ahora:", len(q_src),
          "| MPANT en Existencias:", len(q_dest))
print("LISTO")
