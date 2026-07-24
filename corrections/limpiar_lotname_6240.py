# Limpia el lot_name huerfano HMC54072602 de la linea de ajuste 6240 (sin lote,
# done) que inflaba la numeracion de SPHMC54. No toca cantidades.
# Autorizado por Fernando 2026-07-20.
ml = env['stock.move.line'].sudo().browse(6240)
assert ml.exists() and not ml.lot_id and ml.lot_name == 'HMC54072602', 'linea inesperada'
ml.write({'lot_name': False})
print('Linea 6240 lot_name ->', repr(ml.lot_name))
env.cr.commit()
# verificar numeracion y stock
prod = env['product.product'].search([('default_code','=','SPHMC54')], limit=1)
print('Proximo lote SPHMC54:', prod._amunet_next_lot_names(1)[0])
q = env['stock.quant'].sudo().search([('product_id','=',prod.id),('location_id','=',5),('quantity','!=',0)])
print('Stock SPHMC54 Existencias:', [(x.lot_id.name or 'sin lote', x.quantity) for x in q])
