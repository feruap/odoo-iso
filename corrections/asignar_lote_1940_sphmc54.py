# Asigna el lote HMC54042601 (id 1180) a los 19.40 cm reales de SPHMC54 que
# estaban en AMP/Existencias sin lote (ajuste de Karla del 1-jul), y corrige la
# linea 5482 para eliminar el nombre huerfano HMC54072602 que inflaba la
# numeracion. Autorizado por Fernando 2026-07-20.
lot = env['stock.lot'].browse(1180)
assert lot.exists() and lot.name == 'HMC54042601', 'lote destino inesperado'
q = env['stock.quant'].sudo().browse(4172)
assert q.exists() and q.product_id.default_code == 'SPHMC54' and not q.lot_id and abs(q.quantity - 19.40) < 0.01, 'quant inesperado'
q.write({'lot_id': lot.id})
print('Quant 4172 -> lote', q.lot_id.name, '| qty', q.quantity)
# corregir la linea del ajuste (done) para quitar el nombre huerfano
ml = env['stock.move.line'].sudo().browse(5482)
try:
    ml.write({'lot_id': lot.id, 'lot_name': lot.name})
    print('Linea 5482 -> lote', ml.lot_id.name)
except Exception as e:
    try:
        ml.write({'lot_name': lot.name})
        print('Linea 5482: solo lot_name ->', ml.lot_name, '(lot_id no editable:', str(e)[:50], ')')
    except Exception as e2:
        print('Linea 5482 NO editable:', str(e2)[:80])
env.cr.commit()
print('COMMIT')
