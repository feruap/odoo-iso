# -*- coding: utf-8 -*-
# Consolidacion de lote del cartucho MPCAC08 (recepcion AMP/IN/00190): llego mas
# de lo planeado (mismo lote de proveedor DOA-455) y se capturo mal como 2 lotes
# Amunet (CAC08072601=980, CAC08072602=700). Debe ser UN solo lote de 1680. Se
# reasignan los 700 al lote CAC08072601 y se archiva CAC08072602. Ambos estan en
# cuarentena (pending), sin liberar. Autorizado por Fernando 2026-07-16.
from odoo import fields
MoveLine = env['stock.move.line'].sudo()
Lot = env['stock.lot'].sudo()
Prod = env['product.product']
Quant = env['stock.quant'].sudo()

prod = Prod.search([('default_code', '=', 'MPCAC08')], limit=1)
lot_keep = Lot.search([('product_id', '=', prod.id), ('name', '=', 'CAC08072601')], limit=1)
lot_drop = Lot.search([('product_id', '=', prod.id), ('name', '=', 'CAC08072602')], limit=1)


def qty(lot):
    return sum(Quant.search([('lot_id', '=', lot.id),
                             ('location_id.usage', '=', 'internal')]).mapped('quantity'))

print('ANTES  -> CAC08072601: %s | CAC08072602: %s' % (qty(lot_keep), qty(lot_drop)))

# 1) Reasignar la(s) linea(s) de recepcion del lote drop -> keep (historial).
ml = MoveLine.search([('lot_id', '=', lot_drop.id)])
print('lineas a reasignar:', ml.ids, '| qty:', ml.mapped('quantity'))
ml.with_context(_amunet_line_no_propagate=True).write({'lot_id': lot_keep.id})
env.flush_all()

# 2) Fallback: si el write no movio el quant, mover el stock manualmente.
resto = qty(lot_drop)
if resto > 0:
    q = Quant.search([('lot_id', '=', lot_drop.id), ('quantity', '>', 0),
                      ('location_id.usage', '=', 'internal')], limit=1)
    Quant._update_available_quantity(prod, q.location_id, -q.quantity, lot_id=lot_drop)
    Quant._update_available_quantity(prod, q.location_id, q.quantity, lot_id=lot_keep)
    env.flush_all()
    print('fallback quant aplicado (%s u)' % q.quantity)

print('DESPUES-> CAC08072601: %s | CAC08072602: %s' % (qty(lot_keep), qty(lot_drop)))

# 3) El lote CAC08072602 queda en 0 (no se elimina: tiene historial/FK). Es
#    inofensivo — no aparece en existencias.
print('lote CAC08072602 queda vacio (0), sin stock. No se elimina por historial.')

env.flush_all()
env.cr.commit()
