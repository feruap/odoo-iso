# -*- coding: utf-8 -*-
# Traslado a AMP/Existencias de los lotes ya liberados (SPHMC75/76 y STBPR01),
# que estaban en AMP/Entrada y AMP/Entrada/Control de calidad. Traslado interno
# auditable (stock.move done). Autorizado por Fernando 2026-07-16.
# El lote ya esta liberado: el candado de expediente bloquea escrituras. El
# traslado a Existencias es logistica (no cambia el expediente), por eso se usa
# skip_lot_release_lock (mismo flag que el sistema usa al liberar).
env = env(context=dict(env.context, skip_lot_release_lock=True))
Move = env['stock.move'].sudo()
Quant = env['stock.quant'].sudo()
MoveLine = env['stock.move.line'].sudo()
Prod = env['product.product']
Lot = env['stock.lot'].sudo()
amp_exist = env['stock.location'].browse(5)  # AMP/Existencias

for code, lname in [('SPHMC75', 'HMC75072601'),
                    ('SPHMC76', 'HMC76072601'),
                    ('STBPR01', 'BPR01072601')]:
    prod = Prod.search([('default_code', '=', code)], limit=1)
    lot = Lot.search([('product_id', '=', prod.id), ('name', '=', lname)], limit=1)
    q = Quant.search([('lot_id', '=', lot.id), ('quantity', '>', 0),
                      ('location_id.usage', '=', 'internal')], limit=1)
    if not q:
        print('SIN stock:', code); continue
    src = q.location_id
    qty = q.quantity
    if src.id == amp_exist.id:
        print('ya en Existencias:', code); continue
    mv = Move.create({
        'description_picking': 'Traslado a Existencias %s' % lname,
        'product_id': prod.id, 'product_uom_qty': qty,
        'product_uom': prod.uom_id.id,
        'location_id': src.id, 'location_dest_id': amp_exist.id,
    })
    mv._action_confirm()
    mv._action_assign()
    if mv.move_line_ids:
        mv.move_line_ids.write({'lot_id': lot.id, 'quantity': qty})
    else:
        MoveLine.create({'move_id': mv.id, 'product_id': prod.id, 'lot_id': lot.id,
                         'quantity': qty, 'location_id': src.id,
                         'location_dest_id': amp_exist.id})
    mv.picked = True
    mv._action_done()
    # Flush dentro del contexto skip para que el recalculo de fechas del lote
    # (use/removal/alert_date, bloqueadas al estar liberado) no dispare el candado.
    env.flush_all()
    q2 = Quant.search([('lot_id', '=', lot.id), ('quantity', '>', 0),
                       ('location_id.usage', '=', 'internal')], limit=1)
    print('MOVIDO %s: %s -> %s (%s) | ahora en: %s' % (
        code, src.complete_name, amp_exist.complete_name, qty,
        q2.location_id.complete_name if q2 else '?'))
env.flush_all()
env.cr.commit()
