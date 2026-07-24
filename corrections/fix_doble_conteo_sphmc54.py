# Corrige el doble conteo de SPHMC54 en AMP/Existencias: deja sin-lote=0 y
# HMC54042601=19.40 via ajuste de inventario. Autorizado por Fernando 2026-07-20.
prod = env['product.product'].search([('default_code', '=', 'SPHMC54')], limit=1)
LOC = 5  # AMP/Existencias
Q = env['stock.quant'].sudo()
q_nolot = Q.search([('product_id', '=', prod.id), ('location_id', '=', LOC), ('lot_id', '=', False)])
q_lot = Q.search([('product_id', '=', prod.id), ('location_id', '=', LOC), ('lot_id', '=', 1180)])
print('Antes: sin-lote=%s | HMC54042601=%s' % (q_nolot.mapped('quantity'), q_lot.mapped('quantity')))
for q, target in [(q_nolot, 0.0), (q_lot, 19.40)]:
    if q:
        q.with_context(inventory_mode=True).write({'inventory_quantity': target})
        q.action_apply_inventory()
# releer
q_nolot = Q.search([('product_id', '=', prod.id), ('location_id', '=', LOC), ('lot_id', '=', False)])
q_lot = Q.search([('product_id', '=', prod.id), ('location_id', '=', LOC), ('lot_id', '=', 1180)])
print('Despues: sin-lote=%s | HMC54042601=%s' % (q_nolot.mapped('quantity'), q_lot.mapped('quantity')))
env.cr.commit()
print('COMMIT')
